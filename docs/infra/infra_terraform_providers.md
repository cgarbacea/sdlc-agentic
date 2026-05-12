---
tags: [Terraform, provider, backend, remote state, S3, pin versions, workspace, required_version]
executor: infra
---

# Terraform Provider and Backend Configuration

```hcl
# providers.tf — always pin all provider versions
terraform {
  required_version = ">= 1.6.5"

  required_providers {
    # Pin with ~> (allows patch updates, blocks minor version jumps)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.16"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  # Remote state — adapt backend type to the cloud (s3 / azurerm / gcs / remote)
  # Never use local state in a team
  backend "s3" {
    bucket               = "<project>-terraform-state"
    key                  = "terraform.tfstate"
    workspace_key_prefix = "env"   # isolates state per environment
    region               = "<region>"
  }
}
```

## Rules

- All provider versions pinned with `~>` — never unpinned
- Remote backend always configured — never local `terraform.tfstate` in a team
- Use `terraform.workspace` to select environment: `dev`, `qa`, `stage`, `prod`
- `workspace_key_prefix` isolates state per environment in the same bucket
