---
tags: [Helm, ExternalSecret, K8s, secrets, v1beta1, refreshInterval, deletionPolicy, deployment template]
executor: be_module
---

# Helm Chart Pattern — ExternalSecret v1beta1

## ExternalSecret Template

```yaml
# .charts/<service>/templates/externalsecret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {{ include "<service>.fullname" . }}-secrets
  labels:
    {{- include "<service>.labels" . | nindent 4 }}
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager
  target:
    name: {{ .Values.secretName }}
    creationPolicy: Owner
    deletionPolicy: Retain       # keeps K8s Secret if ExternalSecret is deleted
  data:
    - secretKey: DB_USERNAME
      remoteRef:
        key: {{ .Values.externalSecret.dbSecretKey }}
        property: username
    - secretKey: DB_PASSWORD
      remoteRef:
        key: {{ .Values.externalSecret.dbSecretKey }}
        property: password
```

## Deployment Template

```yaml
containers:
  - name: <service>
    image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
    env:
      - name: DB_HOST
        value: {{ .Values.config.db.host | quote }}   # non-secret config: direct value
      - name: DB_USERNAME
        valueFrom:
          secretKeyRef:
            name: {{ .Values.secretName }}            # from ExternalSecret
            key: DB_USERNAME
    livenessProbe:
      {{- toYaml .Values.livenessProbe | nindent 12 }}  # from values.yaml
    resources:
      {{- toYaml .Values.resources | nindent 12 }}
```

## Rules

- Use `external-secrets.io/v1beta1` — **never** `kubernetes-client.io/v1` (deprecated)
- `deletionPolicy: Retain` — prevents accidental secret deletion
- `refreshInterval: 1h` — secrets re-sync on schedule, not only at pod restart
- Non-secret config as direct `value:` — only credentials go in secrets
- `livenessProbe`, `readinessProbe`, `resources` always from `values.yaml` — not hardcoded
