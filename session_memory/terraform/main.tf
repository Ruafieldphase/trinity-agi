# =============================================================================
# Agent System - Terraform 메인 설정
# =============================================================================
# 사용법: terraform init && terraform plan && terraform apply
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  # 상태 파일을 S3에 저장 (모든 팀이 공유)
  backend "s3" {
    bucket         = "agent-system-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# =============================================================================
# Provider 설정
# =============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "Agent-System"
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# =============================================================================
# 데이터 소스
# =============================================================================

# EKS 클러스터 인증 토큰
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

# 현재 AWS 계정 정보
data "aws_caller_identity" "current" {}

# 사용 가능한 AZ
data "aws_availability_zones" "available" {
  state = "available"
}

# =============================================================================
# 지역 변수
# =============================================================================

locals {
  cluster_name = "${var.project_name}-${var.environment}-cluster"

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# VPC 및 네트워킹
# =============================================================================

module "vpc" {
  source = "./modules/vpc"

  project_name           = var.project_name
  environment            = var.environment
  vpc_cidr               = var.vpc_cidr
  availability_zones     = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnet_cidrs   = var.private_subnet_cidrs
  public_subnet_cidrs    = var.public_subnet_cidrs
  enable_nat_gateway     = true
  enable_vpn_gateway     = false
  enable_flow_logs       = true

  tags = local.common_tags
}

# =============================================================================
# EKS 클러스터
# =============================================================================

module "eks" {
  source = "./modules/eks"

  cluster_name           = local.cluster_name
  cluster_version        = var.kubernetes_version
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids

  # 노드 그룹 설정
  node_group_desired_size = var.eks_node_group_desired_size
  node_group_min_size     = var.eks_node_group_min_size
  node_group_max_size     = var.eks_node_group_max_size
  node_instance_types     = var.eks_node_instance_types

  # 로깅
  enable_cluster_logging  = true
  log_retention_days      = 30

  tags = local.common_tags
}

# =============================================================================
# RDS PostgreSQL 데이터베이스
# =============================================================================

module "rds" {
  source = "./modules/rds"

  identifier           = "${var.project_name}-${var.environment}-db"
  database_name        = var.database_name
  master_username      = var.database_user
  master_password      = var.database_password

  engine_version       = "15.2"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  storage_type         = "gp3"

  vpc_security_group_ids = [module.security_groups.rds_security_group_id]
  db_subnet_group_name   = module.vpc.db_subnet_group_name

  multi_az             = var.environment == "production" ? true : false
  backup_retention_days = var.environment == "production" ? 30 : 7

  publicly_accessible  = false
  skip_final_snapshot  = var.environment != "production"

  tags = local.common_tags
}

# =============================================================================
# ElastiCache Redis
# =============================================================================

module "elasticache" {
  source = "./modules/elasticache"

  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.environment == "production" ? 3 : 1

  parameter_group_name = "default.redis7"
  port                 = 6379

  security_group_ids   = [module.security_groups.redis_security_group_id]
  subnet_group_name    = module.vpc.elasticache_subnet_group_name

  automatic_failover_enabled = var.environment == "production" ? true : false
  multi_az_enabled           = var.environment == "production" ? true : false

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  tags = local.common_tags
}

# =============================================================================
# 보안 그룹
# =============================================================================

module "security_groups" {
  source = "./modules/security_groups"

  vpc_id           = module.vpc.vpc_id
  project_name     = var.project_name
  environment      = var.environment
  eks_cluster_id   = module.eks.cluster_id

  tags = local.common_tags
}

# =============================================================================
# ECR (Elastic Container Registry)
# =============================================================================

module "ecr" {
  source = "./modules/ecr"

  repository_name = "${var.project_name}/agent-system"

  scan_on_push               = true
  image_tag_mutability       = "MUTABLE"
  image_retention_count      = 10

  tags = local.common_tags
}

# =============================================================================
# IAM 역할 및 정책
# =============================================================================

module "iam" {
  source = "./modules/iam"

  project_name        = var.project_name
  environment         = var.environment
  eks_cluster_name    = module.eks.cluster_name
  ecr_repository_arn  = module.ecr.repository_arn
  rds_instance_arn    = module.rds.db_instance_arn

  tags = local.common_tags
}

# =============================================================================
# CloudWatch 로깅
# =============================================================================

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name    = var.project_name
  environment     = var.environment
  log_retention   = 30

  alarms = {
    eks_cpu_high    = true
    eks_memory_high = true
    rds_cpu_high    = true
    redis_cpu_high  = true
  }

  tags = local.common_tags
}

# =============================================================================
# Outputs
# =============================================================================

output "eks_cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "rds_endpoint" {
  description = "RDS 데이터베이스 엔드포인트"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis 클러스터 엔드포인트"
  value       = module.elasticache.cluster_nodes[0].address
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR 저장소 URL"
  value       = module.ecr.repository_url
}
