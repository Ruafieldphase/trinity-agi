# =============================================================================
# Agent System - Terraform 변수 정의
# =============================================================================

# =============================================================================
# 기본 설정
# =============================================================================

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-\\d{1}$", var.aws_region))
    error_message = "유효한 AWS 리전을 입력하세요."
  }
}

variable "environment" {
  description = "환경 (development, staging, production)"
  type        = string

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "environment는 development, staging, production 중 하나여야 합니다."
  }
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "agent-system"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}[a-z0-9]$", var.project_name))
    error_message = "프로젝트 이름은 3-30자, 소문자 및 하이픈만 사용 가능합니다."
  }
}

# =============================================================================
# VPC 및 네트워킹
# =============================================================================

variable "vpc_cidr" {
  description = "VPC CIDR 블록"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "유효한 CIDR 블록을 입력하세요."
  }
}

variable "public_subnet_cidrs" {
  description = "공개 서브넷 CIDR 블록 리스트"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "프라이빗 서브넷 CIDR 블록 리스트"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

# =============================================================================
# EKS 클러스터
# =============================================================================

variable "kubernetes_version" {
  description = "Kubernetes 버전"
  type        = string
  default     = "1.28"

  validation {
    condition     = can(regex("^1\\.\\d{2}$", var.kubernetes_version))
    error_message = "유효한 Kubernetes 버전을 입력하세요 (예: 1.28)."
  }
}

variable "eks_node_group_desired_size" {
  description = "EKS 노드 그룹 원하는 크기"
  type        = number
  default     = 3

  validation {
    condition     = var.eks_node_group_desired_size >= 1 && var.eks_node_group_desired_size <= 100
    error_message = "노드 그룹 크기는 1-100 사이여야 합니다."
  }
}

variable "eks_node_group_min_size" {
  description = "EKS 노드 그룹 최소 크기"
  type        = number
  default     = 2
}

variable "eks_node_group_max_size" {
  description = "EKS 노드 그룹 최대 크기"
  type        = number
  default     = 10
}

variable "eks_node_instance_types" {
  description = "EKS 노드 인스턴스 타입 리스트"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

# =============================================================================
# RDS 데이터베이스
# =============================================================================

variable "database_name" {
  description = "기본 데이터베이스 이름"
  type        = string
  default     = "agent_system"
}

variable "database_user" {
  description = "데이터베이스 마스터 사용자명"
  type        = string
  default     = "admin"

  sensitive = true
}

variable "database_password" {
  description = "데이터베이스 마스터 비밀번호"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_password) >= 8 && can(regex("[A-Z]", var.database_password)) && can(regex("[0-9]", var.database_password)) && can(regex("[^a-zA-Z0-9]", var.database_password))
    error_message = "비밀번호는 최소 8자이며 대문자, 숫자, 특수문자를 포함해야 합니다."
  }
}

variable "db_instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.db_instance_class))
    error_message = "유효한 RDS 인스턴스 클래스를 입력하세요."
  }
}

variable "db_allocated_storage" {
  description = "할당된 스토리지 (GB)"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "스토리지는 20-1000 GB 사이여야 합니다."
  }
}

# =============================================================================
# ElastiCache Redis
# =============================================================================

variable "redis_node_type" {
  description = "Redis 노드 타입"
  type        = string
  default     = "cache.t3.micro"

  validation {
    condition     = can(regex("^cache\\.[a-z0-9]+\\.[a-z0-9]+$", var.redis_node_type))
    error_message = "유효한 Redis 노드 타입을 입력하세요."
  }
}

variable "redis_auth_token" {
  description = "Redis 인증 토큰"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.redis_auth_token) >= 16
    error_message = "Redis 인증 토큰은 최소 16자여야 합니다."
  }
}

# =============================================================================
# 태그
# =============================================================================

variable "tags" {
  description = "모든 리소스에 적용할 태그"
  type        = map(string)
  default = {
    Project     = "Agent-System"
    ManagedBy   = "Terraform"
    CostCenter  = "Engineering"
  }
}
