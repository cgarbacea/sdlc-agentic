---
tags: [naming, tags, resource names, locals, workspace, convention, cost tracking]
executor: infra
---

# Terraform Naming Convention

```hcl
# locals.tf — all resource names derived from workspace + project name
locals {
  name = "my-service"   # short, kebab-case project name

  # Pattern: <env>-<project>-<resource-type>
  # e.g. dev-my-service-vpc, prod-my-service-db, staging-my-service-cluster

  # Every resource gets this tag set — enables cost allocation and filtering
  tags = {
    Environment = terraform.workspace
    Project     = local.name
    ManagedBy   = "terraform"   # or "pulumi", "cdk"
  }
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # merge() allows per-resource name without losing standard tags
  tags = merge(local.tags, { Name = "${terraform.workspace}-${local.name}-vpc" })
}
```

## Rules

- Never hardcode environment strings — always derive from workspace/variable
- Every resource gets the standard tag/label set — no exceptions
- Short but meaningful names — `my-service` not `ms` or `my-digital-health-platform-backend-service`
- Consistent pattern across all resource types makes the console navigable
