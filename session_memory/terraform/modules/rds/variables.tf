variable "identifier" {
  type = string
  description = "RDS 인스턴스 식별자"
}

variable "database_name" {
  type = string
  description = "기본 데이터베이스 이름"
}

variable "master_username" {
  type = string
  description = "마스터 사용자명"
  sensitive = true
}

variable "master_password" {
  type = string
  description = "마스터 비밀번호"
  sensitive = true
}

variable "engine_version" {
  type = string
  default = "15.2"
  description = "PostgreSQL 엔진 버전"
}

variable "instance_class" {
  type = string
  default = "db.t3.micro"
  description = "DB 인스턴스 클래스"
}

variable "allocated_storage" {
  type = number
  default = 20
  description = "할당된 스토리지 (GB)"
}

variable "storage_type" {
  type = string
  default = "gp3"
  description = "스토리지 타입"
}

variable "db_subnet_group_name" {
  type = string
  description = "DB 서브넷 그룹 이름"
}

variable "security_group_ids" {
  type = list(string)
  description = "보안 그룹 ID 목록"
}

variable "multi_az" {
  type = bool
  default = false
  description = "Multi-AZ 배포 여부"
}

variable "publicly_accessible" {
  type = bool
  default = false
  description = "공개 접근 가능 여부"
}

variable "backup_retention_days" {
  type = number
  default = 7
  description = "백업 보관 기간 (일)"
}

variable "skip_final_snapshot" {
  type = bool
  default = false
  description = "최종 스냅샷 스킵 여부"
}

variable "enable_enhanced_monitoring" {
  type = bool
  default = true
  description = "향상된 모니터링 활성화 여부"
}

variable "enable_read_replica" {
  type = bool
  default = false
  description = "읽기 전용 복제본 활성화 여부"
}

variable "read_replica_instance_class" {
  type = string
  default = "db.t3.micro"
  description = "읽기 복제본 인스턴스 클래스"
}

variable "enable_cluster_mode" {
  type = bool
  default = false
  description = "클러스터 모드 활성화 여부"
}

variable "enable_snapshot_copy" {
  type = bool
  default = false
  description = "스냅샷 복사 활성화 여부"
}

variable "source_region" {
  type = string
  default = "ap-northeast-1"
  description = "소스 리전"
}

variable "tags" {
  type = map(string)
  description = "태그"
}
