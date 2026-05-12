# Keycloak Migration — NextJS Frontend (admin-portal)

> Based on code analysis of `platform-monorepo/apps/admin-portal` (April 2026).

---

## How auth actually works today (important — it's NOT OAuth2 redirect)

The FE does **not** use the Cognito Hosted UI or OAuth2 authorization code redirect flow.
Despite `AUTHORIZATION_URL` / `IDP_CLIENT_ID` / `IDP_CLIENT_ID_REDIRECT_URL` being in `.env`, **none of those values are read by any component** — they are injected into `window.__ENV__` via the runtime config but never consumed. They are dead config, likely a leftover from a planned or previous implementation.

### The real login flow (confirmed from network trace)

```
LoginForm (email + password)
  → POST /user-management/authorizations/authorize  { email, password }
      → CoachOnboardingServiceImpl.login()
          → CognitoIdentityAdaptorImpl.getAccessToken(email, password)
              → Cognito AdminInitiateAuth (ADMIN_USER_PASSWORD_AUTH)
                  → returns Cognito accessToken (+ refreshToken from SDK, but discarded)
          → fetchUserIdFromToken(accessToken)  ← JWT sub
          → userManagementService.updateUserLastLogin(userId)
      → returns { accessToken }   ← refreshToken is NOT returned today
  → authStore.setTokens({ accessToken, refreshToken: '' })
      → Zustand persist → localStorage["auth-storage"]
      → document.cookie["accessToken"] = token       (for Next.js middleware)
  → GET /user-management/users/profile
  → authStore.login(tokens, user)
      → document.cookie["userStatus"] = user.status
  → KyHttpClient.beforeRequest hook reads token from authStore
      → sets Authorization: Bearer <token> on every API call
  → 401 response → authStore.logout() + window.location.href = '/'
```

**Key facts:**

- This is **Resource Owner Password Credentials** (ROPC) — not OAuth2 Authorization Code, no redirects.
- The Cognito SDK `AdminInitiateAuthResponse` does include a `refreshToken`, but `CoachOnboardingServiceImpl.login()` only maps `accessToken` into `AuthorizationResponseDto`. The refresh token is silently discarded.
- `AuthService.refreshToken()` on the FE throws `"Token refresh not implemented"` and is never called.
- Users are hard-logged-out when the access token expires (Cognito default: **1 hour**).

### Sendbird messaging legacy keys

`features/messaging/utils/messaging.ts` reads two localStorage keys:

- `AUTHENTICATION_TOKEN` — legacy token key from a previous implementation, used as fallback
- `IDP_CLIENT_INFO` — JSON object with `{ sub: "<userId>" }`, read to get coach user ID for Sendbird

These were set by an older Amplify/Cognito integration and are now only fallbacks. Primary source is `auth-storage` (Zustand persist).

---

## What the FE migration actually requires

Because the FE calls the **backend** for authentication (not Cognito directly), most of the auth migration work happens on the backend (`user-management-service`). The FE impact is smaller than expected.

---

## Changes required

### 1. No changes needed

| Item                                                  | Reason                                                    |
| ----------------------------------------------------- | --------------------------------------------------------- |
| `LoginForm` component                                 | Unchanged — still posts email+password                    |
| `KyHttpClient` (token injection, 401 handling)        | Unchanged — reads from `authStore`, provider-agnostic     |
| `authStore` (Zustand)                                 | Unchanged — stores whatever tokens the backend returns    |
| Cookie logic (`setAuthCookie`, `setUserStatusCookie`) | Unchanged                                                 |
| Next.js middleware (`proxy.ts`)                       | Unchanged — checks `accessToken` cookie, no IDP knowledge |
| All API service classes                               | Unchanged — use `KyHttpClient`                            |
| `AUTHORIZATION_URL` / `IDP_CLIENT_ID` env vars        | Currently unused — can be repurposed or removed           |

### 2. Token refresh — MUST implement

This is the most important FE task regardless of Cognito vs Keycloak, and it requires **both a BE and FE change**.

Currently on `accessToken` expiry (1h default), users get a hard `401 → logout → redirect to /`. The fix requires two parts:

**A) Backend — fix `authorizations/authorize` to return `refreshToken`**

`CoachOnboardingServiceImpl.login()` already receives the refresh token from `AdminInitiateAuthResponse.authenticationResult().refreshToken()` but discards it. Fix `AuthorizationResponseDto` and the login method:

```java
// AuthorizationResponseDto.java — add refreshToken field
public record AuthorizationResponseDto(String accessToken, String refreshToken) {}

// CoachOnboardingServiceImpl.login() — pass through refreshToken
public AuthorizationResponseDto login(CognitoUserLoginDto login) {
    var result = cognitoClient.getAuthResult(login.email(), login.password()); // refactor getAccessToken to return full result
    userManagementService.updateUserLastLogin(fetchUserIdFromToken(result.accessToken()));
    return new AuthorizationResponseDto(result.accessToken(), result.refreshToken());
}
```

For Keycloak, the equivalent is the `refresh_token` field in the token endpoint response.

**B) Backend — add `POST /authorizations/refresh` endpoint**

- Accepts `{ refreshToken: string }`
- **Cognito:** calls `InitiateAuth` with `REFRESH_TOKEN_AUTH` grant
- **Keycloak:** calls `POST /realms/{realm}/protocol/openid-connect/token` with `grant_type=refresh_token`
- Returns new `{ accessToken, refreshToken }`

B) **Frontend** — implement `AuthService.refreshToken()` and wire it into `KyHttpClient.afterResponse`:

```ts
// ky-http-client.ts — afterResponse hook (replace current 401 handling)
if (response.status === 401 && typeof window !== "undefined") {
  const refreshToken = useAuthStore.getState().getRefreshToken();
  if (refreshToken) {
    try {
      const newTokens = await authService.refreshToken(refreshToken);
      useAuthStore.getState().setTokens(newTokens);
      // Retry the original request with the new token
      request.headers.set("Authorization", `Bearer ${newTokens.accessToken}`);
      return ky(request);
    } catch {
      // Refresh failed — force logout
    }
  }
  useAuthStore.getState().logout();
  window.location.href = "/";
}
```

```ts
// AuthService.ts — implement refreshToken
async refreshToken(refreshToken: string): Promise<AuthTokens> {
  const response = await this.http.post<LoginApiResponse>('authorizations/refresh', {
    json: { refreshToken },
  });
  return {
    accessToken: response.accessToken,
    refreshToken: response.refreshToken || '',
  };
}
```

### 3. `IDP_CLIENT_INFO` localStorage key — check and clean up

`getCoachUserIdFromStorage()` in `messaging/utils/messaging.ts` reads `localStorage.getItem('IDP_CLIENT_INFO')` and parses `{ sub }` from it to get the coach user ID for Sendbird.

This key was set by the old Amplify SDK — it will **not** be present after Keycloak migration. The code already falls back to `authStoreUserId` (`user.userId` from `authStore`), so it should work without it.

**Action:** Verify in a test environment that Sendbird channels resolve correctly using only the `authStore` user ID fallback. Once confirmed, remove the `IDP_CLIENT_INFO` localStorage read.

### 4. `AUTHENTICATION_TOKEN` localStorage fallback — remove

In `messaging/utils/messaging.ts`, `getTokenFromStorage()` reads `localStorage.getItem('AUTHENTICATION_TOKEN')` as a legacy fallback. This was set by old Amplify. After migration it will always be null and the code falls through to `auth-storage` correctly.

**Action:** Remove the `AUTHENTICATION_TOKEN` fallback read and simplify `resolveAuthContext()` once confirmed the Amplify legacy keys are gone everywhere.

### 5. Dead env vars — repurpose or remove

`AUTHORIZATION_URL`, `IDP_CLIENT_ID`, `IDP_CLIENT_ID_REDIRECT_URL` are in `.env`, `layout.tsx`, and `lib/config/index.ts` but never consumed by any component.

**Options:**

- **Remove them** — clean up `runtimeConfig` in `layout.tsx` and `Window.__ENV__` type
- **Repurpose** — if a future self-service password reset or direct Keycloak login page is needed, these could point to the Keycloak realm login URL and client ID

For now: remove to avoid confusion.

**Files to update:**

- [app/[lng]/layout.tsx](../platform-monorepo/apps/admin-portal/app/[lng]/layout.tsx) — remove 3 fields from `runtimeConfig`
- [app/share/layout.tsx](../platform-monorepo/apps/admin-portal/app/share/layout.tsx) — same
- [lib/config/index.ts](../platform-monorepo/apps/admin-portal/lib/config/index.ts) — remove from `Window.__ENV__` type and `appConfig` getters
- `.env.example`, `.env.local`, `.env.stg` — remove the 3 vars

---

## Env vars — before / after

```bash
# BEFORE
AUTHORIZATION_URL=https://us-east-1zax93ixbk.auth.us-east-1.amazoncognito.com/login  # ← unused, remove
IDP_CLIENT_ID=7ajjdhi1tmkl5gcg3o8282drur                                               # ← unused, remove
IDP_CLIENT_ID_REDIRECT_URL=https://staff-portal-dev.digitalhealth.dev                 # ← unused, remove
API_BASE_URL=https://bh5o1kah8c.execute-api.us-east-1.amazonaws.com                   # ← stays, points to backend API gateway

# AFTER (no new vars needed — auth is backend-delegated)
API_BASE_URL=https://<new-api-gateway-or-ingress>                                      # ← update to new infra URL
```

No new FE env vars are needed for Keycloak because the FE never talks to Keycloak directly.

---

## Migration effort summary

| Task                                                                  | Owner    | Effort  | Blocked by                        |
| --------------------------------------------------------------------- | -------- | ------- | --------------------------------- |
| BE: fix `AuthorizationResponseDto` to include `refreshToken`          | Java dev | Trivial | Nothing — can do now with Cognito |
| BE: add `POST /authorizations/refresh` endpoint                       | Java dev | Low     | Nothing — can do now with Cognito |
| FE: implement `AuthService.refreshToken()`                            | FE dev   | Low     | BE endpoint above                 |
| FE: wire refresh into `KyHttpClient` 401 handler                      | FE dev   | Low     | `AuthService.refreshToken()`      |
| BE: swap `CognitoIdentityAdaptorImpl` → `KeycloakIdentityAdaptorImpl` | Java dev | Medium  | Keycloak setup done               |
| Verify Sendbird `IDP_CLIENT_INFO` fallback works                      | FE dev   | Trivial | Keycloak user migration done      |
| Remove dead `AUTHENTICATION_TOKEN` / `IDP_CLIENT_INFO` reads          | FE dev   | Trivial | After verification                |
| Remove `AUTHORIZATION_URL` / `IDP_CLIENT_ID` env vars and config      | FE dev   | Trivial | Any time                          |

> The first two BE tasks can be done **today against Cognito** — they don't require Keycloak to be ready and immediately fix the 1-hour session expiry problem.

**Total FE work: ~0.5–1 day**, almost entirely the token refresh wiring.
The login/logout/profile/API call flows require zero changes.

---

## What is ROPC and why it matters

**Resource Owner Password Credentials (ROPC)** is an OAuth2 grant type where the user's email and password are collected directly by the application and sent to the authorization server in exchange for a token.

Today the flow is:

```
FE collects email + password
  → sends them to the backend (POST /authorizations/authorize)
      → backend sends them to Cognito (AdminInitiateAuth)
          → Cognito returns the token
```

The credentials travel through **two hops** before reaching the identity provider — FE → BE → IdP. This means the backend is handling plaintext passwords in transit, which is an anti-pattern. ROPC itself is also considered a legacy flow by the OAuth2 working group (deprecated in OAuth 2.1) because it requires the application to handle credentials directly instead of delegating to the IdP.

---

## Option B — FE calls Keycloak directly (ROPC, decoupled from BE)

The simplest decoupling: FE posts credentials directly to Keycloak, cutting out the BE proxy entirely.

### What changes

**Flow after:**

```
FE collects email + password
  → POST https://keycloak.../realms/{realm}/protocol/openid-connect/token
       { grant_type=password, client_id, username, password }
       → Keycloak returns { access_token, refresh_token, expires_in }
  → authStore.setTokens(tokens)
  → GET /user-management/users/profile   (unchanged)
  → authStore.login(tokens, user)
```

Token refresh becomes trivial — FE calls the same Keycloak token endpoint with `grant_type=refresh_token`. No BE endpoint needed at all.

### Keycloak client requirement

The Keycloak client used by the FE must be **public** (no client secret) with **Direct access grants: ON**. The FE is a browser app — embedding a client secret in it would be insecure. A public client with ROPC is the correct setup for trusted first-party web apps.

The `AUTHORIZATION_URL` and `IDP_CLIENT_ID` env vars that are currently dead config become live and meaningful:

```bash
# New env vars (replace the dead Cognito ones)
KEYCLOAK_URL=https://keycloak.stg.fdn.insighthealth.io
KEYCLOAK_REALM=dev-staff          # or stage-staff, etc. — per environment
KEYCLOAK_CLIENT_ID=staff-portal   # new public Keycloak client, created by DevOps/Terraform
```

### Files that change

| File                                            | Change                                                                                                                                                                               |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `features/auth/api/AuthService.ts`              | Replace `POST /user-management/authorizations/authorize` with direct Keycloak token endpoint call. Implement `refreshToken()` against same endpoint with `grant_type=refresh_token`. |
| `lib/api/ky-http-client.ts`                     | Wire `refreshToken()` into the 401 handler (same as the current plan).                                                                                                               |
| `lib/config/index.ts`                           | Replace dead `authorizationUrl`/`idpClientId` fields with `keycloakUrl`, `keycloakRealm`, `keycloakClientId`.                                                                        |
| `app/[lng]/layout.tsx` + `app/share/layout.tsx` | Replace 3 old env vars with 3 new Keycloak vars in `runtimeConfig`.                                                                                                                  |
| `.env.example`, `.env.local`, `.env.stg`        | Update env vars.                                                                                                                                                                     |

### What stays the same

- `LoginForm` component — unchanged, still collects email + password
- `authStore` — unchanged, still stores tokens
- Cookie logic and Next.js middleware — unchanged
- All API calls with `Authorization: Bearer` — unchanged
- `GET /user-management/users/profile` — unchanged

### BE changes no longer needed under Option B

| Task                                                | Status under Option B                          |
| --------------------------------------------------- | ---------------------------------------------- |
| `POST /authorizations/refresh` endpoint             | ❌ Not needed — FE calls Keycloak directly     |
| `AuthorizationResponseDto` returning `refreshToken` | ❌ Not needed — endpoint is bypassed           |
| `POST /authorizations/authorize` endpoint           | Can be kept for internal tooling or deprecated |

### What happens to `updateUserLastLogin()`

`CoachOnboardingServiceImpl.login()` calls `userManagementService.updateUserLastLogin(userId)` after every login. Under Option B the BE login endpoint is no longer called from the FE.

Options:

- **Add a lightweight `POST /users/last-login` endpoint** the FE calls after receiving a Keycloak token (fire-and-forget)
- **Use a Keycloak event listener SPI** that triggers on login events — no FE call needed
- **Drop it** if last-login tracking is not a business requirement

### Effort comparison

| Task                                           | Option A (BE proxy)        | Option B (FE direct)                                 |
| ---------------------------------------------- | -------------------------- | ---------------------------------------------------- |
| BE: `KeycloakIdentityAdaptorImpl` login method | Medium                     | Low (just remove ROPC proxy, keep user mgmt methods) |
| BE: `POST /authorizations/refresh` endpoint    | Required                   | Not needed                                           |
| FE: `AuthService` changes                      | Low (add refresh only)     | Low (swap login + add refresh)                       |
| FE: env var / config changes                   | Trivial (remove dead vars) | Trivial (replace with Keycloak vars)                 |
| Keycloak: public client setup                  | Not needed                 | Required (DevOps/Terraform)                          |
| Total FE                                       | ~0.5 day                   | ~1 day                                               |
| Total BE                                       | Medium                     | Low–Medium                                           |

Option B is marginally more FE work but **less BE work** overall and results in a cleaner architecture — the backend is no longer involved in the authentication flow, only in user management (creating users, setting passwords, updating attributes).

### Recommendation

If the team accepts a 1-day FE effort, **Option B is the better choice** — it removes the credentials-through-BE anti-pattern, makes token refresh native, and positions the app correctly for a future move to Authorization Code + PKCE if needed.

---

## Onboarding flow — impact analysis

The onboarding is an 8-step flow driven by its own **invitation token** (`X-ONBOARDING-SESSION`), completely separate from the regular login auth. It is **not affected by the Cognito → Keycloak migration on the FE side**.

### How the flow works today

```
Admin sends invite email → user clicks link → /onboarding?X-ONBOARDING-SESSION={token}

Steps 1–2: Intro + Terms
  → no API calls, no auth

Step 3: PasswordSetupStep
  → GET  /user-management/users/onboarding/profile    (X-ONBOARDING-SESSION header, no Bearer token)
  → GET  /user-management/users/onboarding/policy     (X-ONBOARDING-SESSION header)
       ← returns password requirements (currently fetched from Cognito PasswordPolicy)
  → POST /user-management/users/onboarding/generate-otp   (sends OTP to email or phone)
  → POST /user-management/users/onboarding/verify-otp     (submits password + OTP code)
       → BE: validates OTP, calls cognitoClient.setUserPassword() (AdminSetUserPassword)
       → BE: creates user profile in DB
       ← returns { accessToken, refreshToken }   ← Keycloak JWT after migration
  → authStore.setTokens(tokens)   ← user is now logged in

Steps 4–8: Post-login profile setup
  → regular authenticated API calls using the token received above

Step 8: WelcomeStep
  → clears ONBOARDING_AUTHENTICATION_TOKEN from localStorage
  → redirects to /dashboard
```

### Impact per step

| Step                                              | FE change needed | Reason                                                                                         |
| ------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| Steps 1–2                                         | None             | No API calls                                                                                   |
| `GET /onboarding/profile`                         | None             | Reads from DB, no IdP                                                                          |
| `GET /onboarding/policy`                          | None             | FE just displays the values; BE fetches from Cognito today, Keycloak after                     |
| `POST /onboarding/generate-otp`                   | None             | Sends email/SMS via notification service, no IdP                                               |
| `POST /onboarding/verify-otp`                     | None             | FE sends password + OTP code; BE calls `setUserPassword()` on IdP — that's a BE change only    |
| `OTPVerifyResponse { accessToken, refreshToken }` | None             | FE stores both fields already — token issuer changes from Cognito to Keycloak, FE doesn't care |
| Steps 4–8                                         | None             | Regular authenticated calls, unchanged                                                         |
| `X-ONBOARDING-SESSION` token mechanism            | None             | This is your own invitation token, has nothing to do with Cognito or Keycloak                  |

### BE-only change in onboarding

`CoachOnboardingServiceImpl.validateOtp()` calls `cognitoClient.setUserPassword()` — this becomes `keycloakClient.setUserPassword()` in `KeycloakIdentityAdaptorImpl`, which calls:

```
PUT /admin/realms/{realm}/users/{id}/reset-password
```

This is already listed in the main migration plan. No FE involvement.

**Total onboarding FE work: zero.**
