# Keycloak setup

```bash
docker rm -f keycloak-local 2>/dev/null; mkdir -p /Users/cgarbacea/Projects/YOUPAGE/keycloak-data && docker run -d \
  --name keycloak-local \
  -p 8180:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  -e KC_DB=dev-file \
  -v /Users/cgarbacea/Projects/YOUPAGE/keycloak-data:/opt/keycloak/data \
  quay.io/keycloak/keycloak:26.2 \
  start-dev && echo "Container started — waiting for Keycloak to boot..." && sleep 25 && docker logs keycloak-local 2>&1 | grep -E "started in|Listening|ERROR" | tail -5
```

Keycloak is up. Verify and then configure the realm:

```bash
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8180/realms/master && echo " — Keycloak responding"
```

# Create youpage-dev realm via Admin REST API

```bash
TOKEN=$(curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
 -d "client_id=admin-cli&grant_type=password&username=admin&password=admin" \
 | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

echo "Got admin token: ${TOKEN:0:20}..."

# Create realm

```bash
curl -s -o /dev/null -w "Realm create: HTTP %{http_code}\n" \
 -X POST http://localhost:8180/admin/realms \
 -H "Authorization: Bearer $TOKEN" \
 -H "Content-Type: application/json" \
 -d '{"realm":"youpage-dev","enabled":true,"displayName":"YOUPAGE Dev"}'
```

```bash
TOKEN=$(curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
 -d "client_id=admin-cli&grant_type=password&username=admin&password=admin" \
 | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

# Create admin-portal client (public, PKCE, Authorization Code)

```bash
curl -s -o /dev/null -w "Client create: HTTP %{http_code}\n" \
 -X POST http://localhost:8180/admin/realms/youpage-dev/clients \
 -H "Authorization: Bearer $TOKEN" \
 -H "Content-Type: application/json" \
 -d '{
"clientId": "admin-portal",
"enabled": true,
"publicClient": true,
"standardFlowEnabled": true,
"directAccessGrantsEnabled": false,
"redirectUris": ["http://localhost:3000/*","http://localhost:3001/*"],
"webOrigins": ["http://localhost:3000","http://localhost:3001"],
"attributes": {"pkce.code.challenge.method": "S256"}
}'
```

# Create test user

```bash
curl -s -o /dev/null -w "User create: HTTP %{http_code}\n" \
 -X POST http://localhost:8180/admin/realms/youpage-dev/users \
 -H "Authorization: Bearer $TOKEN" \
 -H "Content-Type: application/json" \
 -d '{
"username": "dev",
"email": "dev@youpage.com",
"enabled": true,
"emailVerified": true,
"firstName": "Dev",
"lastName": "User",
"credentials": [{"type":"password","value":"password","temporary":false}]
}'
```

```bash
echo "Done. Verify at http://localhost:8180/admin — realm: youpage-dev"
```

Everything is up and configured. Here's the full status:

---

## Infrastructure ready ✅

### Keycloak

- **URL:** http://localhost:8180
- **Admin console:** http://localhost:8180/admin (admin / admin)
- **Realm:** `youpage-dev`
- **Client:** `admin-portal` (public, PKCE, redirects to localhost:3000 and 3001)
- **Test user:** `dev@youpage.com` / `password`
- **Data persisted to:** keycloak-data (survives container restarts)
- **Restart command:** `docker start keycloak-local`

### PostgreSQL

- **Host:** localhost:5432 (Homebrew, already running)
- **Database:** `youpage_dev`
- **User:** `youpage_app` / `youpage_dev`

---

**Spring resource server config** (goes in `backend-modulith/src/main/resources/application-local.yml`):

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/youpage_dev
    username: youpage_app
    password: youpage_dev
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://localhost:8180/realms/youpage-dev
```
