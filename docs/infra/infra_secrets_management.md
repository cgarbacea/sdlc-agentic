---
tags: [secrets, Secrets Manager, Key Vault, recovery_window, never in files, workload identity, IRSA]
executor: infra
---

# Secrets Management

Principle: **secrets never touch the filesystem or version control**.

```hcl
# secrets.tf (AWS Secrets Manager example)
resource "aws_secretsmanager_secret" "app_config" {
  name = "${terraform.workspace}-${local.name}-config"
  # Dev: 0 (easy recreation) | Production: 7+ (prevents accidental permanent deletion)
  recovery_window_in_days = terraform.workspace == "prod" ? 7 : 0
  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id = aws_secretsmanager_secret.app_config.id
  secret_string = jsonencode({
    DATABASE_URL  = "jdbc:postgresql://${module.db.endpoint}"
    DATABASE_USER = module.db.username
    DATABASE_PASS = random_password.db.result  # generated, never hardcoded
    API_KEY       = var.api_key                # from variable, not inline
  })
}
```

## Never-Do List

- ❌ Secrets in `.tfvars`, `locals.tf`, or any file tracked by git
- ❌ Secrets in K8s `ConfigMap` — use `Secret` or `ExternalSecret`
- ❌ Secrets printed in plan output — mark sensitive variables with `sensitive = true`
- ❌ `recovery_window_in_days = 0` in production
- ❌ Static cloud credentials in pods — use workload identity (IRSA / Workload Identity / Managed Identity)
