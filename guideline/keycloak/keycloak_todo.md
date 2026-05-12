# Keycloak Setup

---

## Keycloak access:

1. **Keycloak base URL** — e.g. `https://keycloak.stg.fdn.insighthealth.io`  
   Must be reachable from wherever you run Terraform (your machine or CI).

2. **Admin service account credentials**

   ⚠️ **The credentials currently provided are insufficient.** The `cronus-admin-portal` client lives in the `saturn` realm and can only manage resources _within_ `saturn`. It cannot create new realms.

   **Currently provided (does NOT work for realm creation):**

   ```
   client_id:     cronus-admin-portal
   client_secret: Y4VDFNtOP2mIaqazTo8M4D0jVpJS9QzO
   realm:         saturn       ← scoped to saturn only
   ```

   **What you need to request from the Keycloak operator:**
   - A new confidential client created in the **`master` realm** (not `saturn`)
   - Its service account must have the **`create-realm`** role assigned (from the `master` realm's built-in `realm-management` client)
   - Provide the `client_id` and `client_secret` for this master realm client

   This is required because one realm per tenant is the correct architecture — each tenant (e.g. Sanofi, Oracle) gets their own isolated realm. A service account in `saturn` has no visibility outside of `saturn` and cannot create peer realms.

3. **Network access** — confirm your IP / CI runner can reach the Keycloak admin port (usually 443 or 8080). If it's behind a VPN or allowlist, get yourself added.

4. **Confirmation that Keycloak is backed by PostgreSQL** (not H2) — H2 is ephemeral, any work you do would be lost on restart. Don't start Terraform work until this is confirmed.

That's it. Everything else — realms, clients, password policies, scopes, secrets — Terraform creates itself. You don't need the operator to pre-create anything beyond a running, accessible Keycloak instance with admin credentials for the `master` realm.

---

## Tooling: Terraform

Use the **`mrparkers/keycloak` Terraform provider** (v4.4+) to manage all Keycloak infrastructure as code. Everything in Steps 2–7 below should be expressed as Terraform resources and committed to the infra repo.

**What Terraform owns:**

- Realm creation and settings
- Password policies
- User profile attributes
- Client definitions and secrets
- Client scopes

**What Terraform does NOT own:**

- User import (bulk data — handled by a Java migration script, coordinated separately with the Java dev)
- Runtime tenant onboarding (future — will be handled by `tenant-configuration-service` via Keycloak Admin API)
- `identity_provider_settings` DB update (Step 10 — Liquibase migration run by Java dev)

Terraform outputs (client secrets, realm URLs) must be stored in the Kubernetes secret store so services can read them at runtime.

---

## Current Cognito inventory (reference)

### Dev environment

| Tenant UUID                            | Tenant name         | Staff pool            | Patient pool          | Staff client ID              |
| -------------------------------------- | ------------------- | --------------------- | --------------------- | ---------------------------- |
| `30e5e533-6f92-4893-8e5d-45b50ebad855` | staff-portal-dev    | `us-east-1_Zax93IXbK` | `us-east-1_KOJSOuE99` | `7ajjdhi1tmkl5gcg3o8282drur` |
| `7d504031-cff9-41be-9b97-ea6c18afc429` | (second dev tenant) | `us-east-1_Zax93IXbK` | `us-east-1_KOJSOuE99` | `7ajjdhi1tmkl5gcg3o8282drur` |
| `7dbd0731-c3ef-46c9-8424-6f88ae457609` | (third dev tenant)  | `us-east-1_O7fq6YYu0` | `us-east-1_KOJSOuE99` | `2pugahprsgs3oc0dcgfnd0esv1` |

### Stage environment

| Tenant UUID                            | Staff pool            | Patient pool          | Staff client ID              |
| -------------------------------------- | --------------------- | --------------------- | ---------------------------- |
| `9aa0266e-0f6d-4d4c-a9d6-26fdf52d8d3c` | `us-east-1_JXeyapDqI` | `us-east-2_pRVm2Nodm` | `13fgkgv2nfb71t5knb56v0br8j` |
| `8744464e-85ee-4cff-a1d0-0d315a34cbfe` | `us-east-1_JXeyapDqI` | `us-east-2_pRVm2Nodm` | `13fgkgv2nfb71t5knb56v0br8j` |

### QA environment

Uses env vars — check running secrets/configmaps for `COGNITO_DOMAIN`, `COGNITO_APP_CLIENT_ID`, `COGNITO_POOL_ENDPOINT`, `COGNITO_EXTERNAL_POOL_ENDPOINT`.

### M2M (service-to-service) Cognito pools

| Service                | Cognito domain                                           | Purpose                      |
| ---------------------- | -------------------------------------------------------- | ---------------------------- |
| `rule-engine-service`  | `us-east-1o7fq6yyu0.auth.us-east-1.amazoncognito.com`    | calls dynamic-survey-service |
| `patient-data-service` | `dev-dhc-sap-hapi-fhir.auth.us-east-1.amazoncognito.com` | calls HAPI FHIR server       |

---

## Important: how the backend uses Keycloak realm names

The backend parses the **last path segment** of `issuerUrl` (stored in `identity_provider_settings`) as the realm identifier, and uses it for all Keycloak Admin API calls.

With Cognito that segment was the pool ID (`us-east-1_Zax93IXbK`). With Keycloak it becomes the **realm name** — so realm names must be agreed before any code is written.

**Naming convention:** `{env}-{tenant-slug}`, lowercase, hyphenated. E.g. `dev-staff`, `stage-patient`.

The issuer URL pattern will be: `https://keycloak.stg.fdn.insighthealth.io/realms/{realm-name}`

---

## Step 1 — Deploy Keycloak

- [ ] Deploy Keycloak **26.x** as a container (minimum 2 replicas for HA)
- [ ] Back it with a dedicated **PostgreSQL** database — not H2, not shared with application DBs
- [ ] Expose it at a stable public URL (e.g. `https://keycloak.stg.fdn.insighthealth.io`) with HTTPS terminated at the ingress/load balancer
- [ ] Store admin credentials in a Kubernetes secret
- [ ] Verify the master realm is reachable and the admin console is accessible before proceeding

---

## Step 2 — Create Realms (one per tenant per environment)

For each tenant, create **two realms**: one for staff/coaches, one for patients.

### Dev — create these realms

| Realm name      | Represents       | Maps to tenant(s)                          |
| --------------- | ---------------- | ------------------------------------------ |
| `dev-staff`     | Coaches / admins | `30e5e533`, `7d504031` (shared pool today) |
| `dev-staff-alt` | Third dev tenant | `7dbd0731`                                 |
| `dev-patient`   | Patients         | All dev tenants (shared pool today)        |

> Realm names must be agreed before Java dev starts — they are used in Admin API calls. Follow the convention above.

### For each realm, configure:

- [ ] Display name, frontend URL, SSL required
- [ ] SMTP settings (host, port, from address, TLS) — required for password reset and email verification emails
- [ ] **User registration**: OFF — users are always created programmatically by `user-management-service`
- [ ] **Forgot password**: ON
- [ ] **Verify email**: ON

---

## Step 3 — Password Policy (per realm)

The backend calls `getPasswordPolicy()` to fetch Cognito's policy and enforces it at signup. Replicate in Keycloak:

In each realm → **Authentication → Password Policy**, add:

- [ ] `Minimum Length` = 8
- [ ] `Uppercase Characters` = 1
- [ ] `Lowercase Characters` = 1
- [ ] `Special Characters` = 1
- [ ] `Digits` = 1
- [ ] `Not Username` (prevent using email as password)
- [ ] `Password History` = 3 (prevents recent reuse)

> Before setting these, verify the exact current Cognito policy by running `aws cognito-idp describe-user-pool` against each pool and checking the `Policies.PasswordPolicy` block.

---

## Step 4 — User Attributes (per realm)

The backend stores and reads `phone_number` and `phone_number_verified` on users. Add these as user attributes in each realm:

For each realm, define two custom user profile attributes:

| Attribute name          | Display name   | Notes                            |
| ----------------------- | -------------- | -------------------------------- |
| `phone_number`          | Phone Number   | Optional E.164 format validation |
| `phone_number_verified` | Phone Verified | Boolean                          |

`email` and `email_verified` are built-in to Keycloak — no action needed for those.

---

## Step 5 — Create the Staff Client (per staff realm)

This client is used by `user-management-service` for the **Resource Owner Password Credentials (ROPC)** login flow — the backend exchanges email+password directly for a token. There are no browser redirects.

For each staff realm, create a **confidential client** (`staff-backend-client`) with:

- [ ] **Direct access grants: ON** — this is the critical setting that enables ROPC
- [ ] Standard flow: OFF
- [ ] Service accounts: OFF
- [ ] Store the generated **client secret** in the Kubernetes secret store

---

## Step 6 — Create the Patient Client (per patient realm)

Same requirements as the staff client — patients also authenticate via the backend ROPC flow.

- [ ] Confidential client (`patient-backend-client`) with **Direct access grants: ON**, Standard flow: OFF
- [ ] Store the generated **client secret** in the Kubernetes secret store

---

## Step 7 — Create M2M Clients (service-to-service)

Two confidential clients for machine-to-machine token fetching. These replace the Cognito resource server / app client used by `rule-engine-service` and `patient-data-service`.

### 7a. `rule-engine-m2m`

Confidential client using **client credentials grant** (no user involved):

- [ ] Service accounts: ON, Standard flow: OFF, Direct access grants: OFF
- [ ] Create a client scope `dynamic-survey:read` and assign it as a default scope on this client
- [ ] Store the generated **client secret** in the Kubernetes secret store

### 7b. `hapi-fhir-m2m`

Same pattern as above:

- [ ] Service accounts: ON, Standard flow: OFF, Direct access grants: OFF
- [ ] Create client scopes `hapi-fhir:read` and `hapi-fhir:operation`, assign both as default scopes
- [ ] Store the generated **client secret** in the Kubernetes secret store

> ⚠️ **HAPI FHIR server also needs to accept Keycloak tokens.** It currently validates Cognito JWTs. Its issuer/JWKS config must be updated to point at the Keycloak realm. Coordinate with the HAPI FHIR operator before cutover.

---

## Step 8 — Export Cognito Users and Import to Keycloak

> This step is handled by a **Java migration script** (not Terraform — Terraform is not suitable for bulk data import). DevOps provides the Keycloak admin credentials and confirms realms exist before the Java dev runs the import.

### 8a. Export from Cognito (DevOps task)

Export all users from each pool using the AWS CLI and hand the JSON files to the Java dev running the migration script. Pools to export:

| Pool ID               | Environment | User type |
| --------------------- | ----------- | --------- |
| `us-east-1_Zax93IXbK` | dev         | staff     |
| `us-east-1_KOJSOuE99` | dev         | patient   |
| `us-east-1_JXeyapDqI` | stage       | staff     |
| `us-east-2_pRVm2Nodm` | stage       | patient   |

### 8b. UUID preservation (critical — tell the Java dev)

The Cognito `Username` field is a UUID and is stored as `user_id` throughout all application databases. The import **must preserve these UUIDs** as the Keycloak user `id`. If new UUIDs are generated, all permission lookups will break for every existing user.

Keycloak's Admin API supports setting a specific `id` on user creation — the Java migration script must use this.

### 8c. Passwords

Cognito does not expose password hashes — passwords cannot be migrated. Choose one of:

**Option A (recommended):** Mark all imported users with a `UPDATE_PASSWORD` required action. On first login to the new system, users are prompted to set a new password via email.

**Option B (zero-downtime):** Implement a Keycloak User Storage SPI that proxies credential validation to Cognito during a transition window. Users are migrated silently on first login. Decommission the SPI once all users have logged in. More complex but avoids a forced password reset for all users at once.

---

## Step 9 — Update Kubernetes Secrets

Terraform outputs the generated client secrets. Store them in the Kubernetes secret store before deploying updated services.

### Secrets to add (per environment)

| Secret key                         | Value source                                                                             | Used by                   |
| ---------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------- |
| `KEYCLOAK_URL`                     | Keycloak host URL                                                                        | `user-management-service` |
| `KEYCLOAK_ADMIN_CLIENT_ID`         | Dedicated admin API client (not `admin-cli`)                                             | `user-management-service` |
| `KEYCLOAK_ADMIN_CLIENT_SECRET`     | Terraform output                                                                         | `user-management-service` |
| `KEYCLOAK_STAFF_CLIENT_ID`         | `staff-backend-client`                                                                   | `user-management-service` |
| `KEYCLOAK_STAFF_CLIENT_SECRET`     | Terraform output (Step 5)                                                                | `user-management-service` |
| `KEYCLOAK_PATIENT_CLIENT_ID`       | `patient-backend-client`                                                                 | `user-management-service` |
| `KEYCLOAK_PATIENT_CLIENT_SECRET`   | Terraform output (Step 6)                                                                | `user-management-service` |
| `KEYCLOAK_M2M_CLIENT_ID`           | `rule-engine-m2m`                                                                        | `rule-engine-service`     |
| `KEYCLOAK_M2M_CLIENT_SECRET`       | Terraform output (Step 7a)                                                               | `rule-engine-service`     |
| `KEYCLOAK_M2M_TOKEN_URI`           | `https://keycloak.stg.fdn.insighthealth.io/realms/{realm}/protocol/openid-connect/token` | `rule-engine-service`     |
| `KEYCLOAK_HAPI_FHIR_CLIENT_ID`     | `hapi-fhir-m2m`                                                                          | `patient-data-service`    |
| `KEYCLOAK_HAPI_FHIR_CLIENT_SECRET` | Terraform output (Step 7b)                                                               | `patient-data-service`    |
| `KEYCLOAK_HAPI_FHIR_TOKEN_URI`     | `https://keycloak.stg.fdn.insighthealth.io/realms/{realm}/protocol/openid-connect/token` | `patient-data-service`    |

### Secrets to remove after cutover

- All `AWS_COGNITO_*` secrets
- `cognito-external-credentials.*`
- `aws.hapi-fhir-cognito.*`

---

## Step 10 — Update the DB (`identity_provider_settings`)

Run per environment **after** realms are created and realm URLs are known. Hand these SQL scripts to the Java dev / DBA.

### Dev

```sql
-- Tenant: 30e5e533 and 7d504031 (both use dev-staff realm)
UPDATE identity_provider_settings
SET
  domain             = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff',
  issuer_url         = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff',
  patient_issuer_url = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-patient',
  client_id          = 'staff-backend-client'
WHERE tenant_id IN (
  '30e5e533-6f92-4893-8e5d-45b50ebad855',
  '7d504031-cff9-41be-9b97-ea6c18afc429'
);

-- Tenant: 7dbd0731 (separate pool today)
UPDATE identity_provider_settings
SET
  domain             = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff-alt',
  issuer_url         = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff-alt',
  patient_issuer_url = 'https://keycloak.stg.fdn.insighthealth.io/realms/dev-patient',
  client_id          = 'staff-backend-client'
WHERE tenant_id = '7dbd0731-c3ef-46c9-8424-6f88ae457609';
```

### Stage

```sql
UPDATE identity_provider_settings
SET
  domain             = 'https://keycloak.stg.fdn.insighthealth.io/realms/stage-staff',
  issuer_url         = 'https://keycloak.stg.fdn.insighthealth.io/realms/stage-staff',
  patient_issuer_url = 'https://keycloak.stg.fdn.insighthealth.io/realms/stage-patient',
  client_id          = 'staff-backend-client'
WHERE tenant_id IN (
  '9aa0266e-0f6d-4d4c-a9d6-26fdf52d8d3c',
  '8744464e-85ee-4cff-a1d0-0d315a34cbfe'
);
```

### QA

Replace env vars `COGNITO_DOMAIN`, `COGNITO_POOL_ENDPOINT`, etc. with the equivalent Keycloak values in the QA configmap/secret, then re-run Liquibase migration.

---

## Step 11 — Smoke Test Checklist

After everything is deployed with Keycloak config:

- [ ] `GET https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff/.well-known/openid-configuration` returns valid JSON
- [ ] `GET https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff/protocol/openid-connect/certs` returns JWKS
- [ ] `POST /user-management/authorizations/authorize` with valid credentials returns a JWT signed by Keycloak
- [ ] JWT `iss` claim = `https://keycloak.stg.fdn.insighthealth.io/realms/dev-staff` (matches `issuer_url` in DB)
- [ ] `GET /user-management/users/profile` with the returned token returns 200 (proves JWT validation works end-to-end)
- [ ] `rule-engine-service` health check passes (M2M token acquisition works)
- [ ] `patient-data-service` health check passes (HAPI FHIR M2M token works)
- [ ] Create a new user via admin portal invite flow (proves `KeycloakIdentityAdaptorImpl.createUser()` works)
- [ ] User can log in with their new password
- [ ] User can change password

---

## Step 12 — Decommission Cognito (after all environments pass smoke test)

- [ ] Disable Cognito user pools (do not delete immediately — keep for rollback)
- [ ] Remove AWS Cognito IAM permissions from service role
- [ ] Archive Cognito user export files
- [ ] Delete Cognito user pools after 30-day hold
- [ ] Remove `aws-java-sdk-cognitoidentity` / `cognitoidentityprovider` from `user-management-service/build.gradle`

---

## Realm naming summary

| Environment | Staff realm   | Patient realm   |
| ----------- | ------------- | --------------- |
| dev         | `dev-staff`   | `dev-patient`   |
| stage       | `stage-staff` | `stage-patient` |
| qa          | `qa-staff`    | `qa-patient`    |
| prod        | `prod-staff`  | `prod-patient`  |

Issuer URL pattern: `https://keycloak.stg.fdn.insighthealth.io/realms/{realm-name}`
