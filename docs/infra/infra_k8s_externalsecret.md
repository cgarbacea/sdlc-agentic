---
tags: [ExternalSecret, K8s secrets, secret injection, v1beta1, deletionPolicy, refreshInterval, ClusterSecretStore]
executor: infra
---

# Kubernetes ExternalSecret Pattern (v1beta1)

```yaml
# Use external-secrets.io/v1beta1 — kubernetes-client.io/v1 is deprecated and unsupported
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: ${namespace}
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager    # or vault, azureKeyVault, gcpSecretsManager
  target:
    name: app-secrets
    creationPolicy: Owner
    deletionPolicy: Retain       # keeps the K8s Secret if this ExternalSecret is deleted
  data:
    - secretKey: DATABASE_URL    # key in the resulting K8s Secret
      remoteRef:
        key: ${secret_name}      # name in the cloud secrets store
        property: DATABASE_URL   # JSON key within the secret value
```

## Rules

- Use `external-secrets.io/v1beta1` — **never** `kubernetes-client.io/v1` (deprecated)
- Secrets never in `ConfigMap` — use `Secret` or `ExternalSecret`
- `deletionPolicy: Retain` — prevents accidental secret deletion when ExternalSecret is removed
- `refreshInterval: 1h` — secrets re-sync on schedule, not only at pod restart
- Each secret property maps to exactly one env var — no blob injection
