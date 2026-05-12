---
tags: [Deployment, K8s, liveness probe, readiness probe, resources, workload identity, IRSA, image tag]
executor: infra
---

# Kubernetes Workload Deployment Pattern

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${service_name}
  namespace: ${namespace}
  labels:
    app: ${service_name}
    version: ${image_tag}
spec:
  replicas: ${replicas}           # from IaC variable, not hardcoded
  selector:
    matchLabels:
      app: ${service_name}
  template:
    spec:
      # Workload identity — pods get cloud permissions without static credentials
      # AWS: IRSA serviceAccountName | Azure: Workload Identity | GCP: Workload Identity
      serviceAccountName: ${service_account}
      containers:
        - name: ${service_name}
          image: ${registry}:${image_tag}   # explicit tag — NEVER :latest
          ports:
            - containerPort: 8080
          envFrom:
            - secretRef:
                name: app-secrets           # from ExternalSecret, not ConfigMap
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          livenessProbe:
            httpGet:
              path: /health/live    # adapt: /actuator/health, /healthz
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 5
```

## Rules

- `resources.requests` and `resources.limits` always both set — prevents noisy-neighbour
- `livenessProbe` and `readinessProbe` always defined — K8s uses them for rolling deploys
- Image tag always explicit — `latest` forbidden in any environment
- Workload identity always used — no static cloud credentials in pods or env vars
