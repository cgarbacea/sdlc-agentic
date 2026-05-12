---
tags: [variables, locals, tfvars, secrets, environment config, sensitive, variable files]
executor: infra
---

# Variables vs Locals vs Environment Files

| Type | Purpose | Example |
|---|---|---|
| `variable` / input | Values that differ per environment | `min_instances`, `cluster_version` |
| `local` / computed | Values derived from inputs | CIDR maps, naming strings, tag maps |
| `tfvars` / config file | Per-environment **non-secret** values | `env-dev.tfvars` |
| Secrets store | All credentials and secrets | DB passwords, API keys, certs |

## Rules

- Never put secrets in variable files — only non-sensitive config
- Secrets go in the cloud secrets store and are referenced by name/ARN at deploy time
- Mark sensitive Terraform variables with `sensitive = true` — suppresses from plan output
- One `.tfvars` file per environment — `env-dev.tfvars`, `env-prod.tfvars`
