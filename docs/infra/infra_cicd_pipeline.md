---
tags: [CI/CD, pipeline, plan, apply, Terraform, separate stages, pin version, plan-out, apply-saved]
executor: infra
---

# CI/CD Pipeline Pattern

Principle: **separate plan from apply, review before execute, pin tool versions**.

## Plan Stage (runs on PR)

```yaml
steps:
  - name: Install IaC tool — pinned version, never inherit from CI environment
    run: |
      curl -sL https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip -o tf.zip
      unzip -o tf.zip -d /usr/local/bin

  - name: Init
    run: terraform init

  - name: Select workspace (idempotent — creates if absent)
    run: terraform workspace select -or-create ${env}

  - name: Plan — save output for apply
    run: terraform plan -var-file="env-${env}.tfvars" -out="${env}.tfplan"
```

## Apply Stage (runs on merge to main)

```yaml
steps:
  - name: Apply saved plan (exact plan reviewed on PR — no surprises)
    run: terraform apply ${env}.tfplan
```

## Rules

- `plan` runs on every PR — reviewers must see what will change before approving
- `apply` runs only on merge to main — never manually in production
- `terraform plan -out=<file>` then `terraform apply <file>` — apply = reviewed plan
- Tool version pinned in the pipeline file — never inherited from CI environment
- Separate pipeline files for plan, apply, and destroy — `destroy` requires explicit trigger, never automatic
