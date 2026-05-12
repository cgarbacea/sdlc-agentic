---
tags: [security, checklist, compliance, secrets, network, containers, IaC hygiene, hardening]
executor: infra
---

# Infrastructure Security Checklist

Before any infrastructure change is complete, verify all of the following.

## Secrets & Credentials

- [ ] No secrets in any IaC file, variable file, or config file tracked by git
- [ ] All secrets stored in cloud secrets store (Secrets Manager / Key Vault / Secret Manager)
- [ ] Workload identity used for cloud API access — no static credentials in pods or env vars
- [ ] Sensitive Terraform variables marked `sensitive = true` — suppressed from plan output

## Network

- [ ] All workloads in private subnets — no direct internet exposure
- [ ] `0.0.0.0/0` ingress only on load balancer ports 80/443
- [ ] Database tier accepts connections only from application security group
- [ ] Bastion/jump host access restricted to specific CIDRs (VPN, office)

## Compute & Containers

- [ ] Container images run as non-root user
- [ ] `latest` image tag never used — all deployments use explicit version tags
- [ ] Resource `requests` and `limits` set on all pods
- [ ] Health probes (`liveness`, `readiness`) defined on all containers

## IaC Hygiene

- [ ] All provider, module, and tool versions pinned
- [ ] Remote state backend configured — no local state files
- [ ] `plan` reviewed and approved before `apply` runs
- [ ] `destroy` never runs automatically — requires explicit trigger
- [ ] Every resource tagged with environment, project, and managed-by
