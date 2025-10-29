# =============================================================================
# Production 환경 Terraform 변수
# =============================================================================

environment = "production"
aws_region  = "ap-northeast-1"

# VPC 설정
vpc_cidr              = "10.0.0.0/16"
public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs  = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

# EKS 설정
kubernetes_version          = "1.28"
eks_node_group_desired_size = 5
eks_node_group_min_size     = 3
eks_node_group_max_size     = 20
eks_node_instance_types     = ["t3.large", "t3.xlarge"]

# RDS 설정 (프로덕션용 고성능)
database_name          = "agent_system"
db_instance_class      = "db.t3.small"
db_allocated_storage   = 100

# Redis 설정 (프로덕션용 고성능)
redis_node_type = "cache.t3.small"

# 태그
tags = {
  Project     = "Agent-System"
  Environment = "Production"
  ManagedBy   = "Terraform"
  CostCenter  = "Engineering"
  Backup      = "daily"
  Monitoring  = "enabled"
}
