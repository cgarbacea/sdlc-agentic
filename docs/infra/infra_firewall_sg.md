---
tags: [security group, firewall, ingress, egress, separate rules, create_before_destroy, minimal ports]
executor: infra
---

# Firewall / Security Group Pattern

```hcl
# firewall.tf (AWS Security Group example)
resource "aws_security_group" "app" {
  name        = "${terraform.workspace}-${local.name}-app"
  description = "App tier — inbound from load balancer only"
  vpc_id      = module.vpc.vpc_id
  tags        = local.tags

  lifecycle {
    create_before_destroy = true   # prevents downtime on rule changes
  }
}

# Separate rule resources — allows targeted changes without recreating the group
resource "aws_security_group_rule" "app_from_lb" {
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.load_balancer.id
  security_group_id        = aws_security_group.app.id
}
```

## Rules

- `0.0.0.0/0` ingress only valid on load balancer (ports 80/443) — never on app or DB tiers
- Separate `aws_security_group_rule` resources — enables targeted changes without recreating the group
- `create_before_destroy = true` on all network/firewall resources — prevents downtime
- Bastion/jump host SSH access restricted to specific CIDRs (VPN, office)
