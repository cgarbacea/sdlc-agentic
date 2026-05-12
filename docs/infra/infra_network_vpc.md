---
tags: [VPC, network, subnet, NAT gateway, private subnets, availability zones, load balancer]
executor: infra
---

# Network / VPC Pattern

Principle: **workloads in private subnets, internet access via NAT, public subnets only for load balancers**.

```hcl
# network.tf (AWS VPC example — adapt to cloud provider)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.19.0"          # always pin module versions

  name = "${terraform.workspace}-${local.name}-vpc"
  cidr = local.vpc_cidr[terraform.workspace]

  # HA: span at least 2 availability zones
  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = local.private_subnet_cidrs  # workloads go here
  public_subnets  = local.public_subnet_cidrs   # load balancers only

  # NAT: single for dev/qa (cost), one-per-AZ for prod (HA)
  enable_nat_gateway = true
  single_nat_gateway = terraform.workspace != "prod"

  # Never auto-assign public IPs to compute instances
  map_public_ip_on_launch = false

  tags = local.tags
}
```

## Rules

- Workloads always in private subnets — never directly internet-accessible
- `single_nat_gateway = true` for dev/qa (cost saving); one-per-AZ for prod (HA)
- Public subnets only for load balancers — tag them for K8s ALB auto-discovery
- Span at least 2 availability zones for HA
