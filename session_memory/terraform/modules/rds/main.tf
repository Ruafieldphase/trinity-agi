# =============================================================================
# RDS 모듈 - PostgreSQL 데이터베이스
# =============================================================================

# DB 서브넷 그룹 (main.tf에서 전달)
# subnet_group_name은 variable로 받음

# =============================================================================
# DB 파라미터 그룹
# =============================================================================

resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "${var.identifier}-params"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_duration"
    value = "on"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "100"  # 100ms 이상 쿼리 로깅
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = var.tags
}

# =============================================================================
# DB 옵션 그룹
# =============================================================================

resource "aws_db_option_group" "postgres" {
  name                     = "${var.identifier}-options"
  option_group_description = "Option group for ${var.identifier}"
  engine_name              = "postgres"
  major_engine_version     = "15"

  tags = var.tags
}

# =============================================================================
# RDS 인스턴스 (PostgreSQL)
# =============================================================================

resource "aws_db_instance" "main" {
  identifier            = var.identifier
  engine                = "postgres"
  engine_version        = var.engine_version
  instance_class        = var.instance_class
  allocated_storage     = var.allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  # 데이터베이스 설정
  db_name  = var.database_name
  username = var.master_username
  password = var.master_password

  # 네트워킹
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.security_group_ids
  publicly_accessible    = var.publicly_accessible

  # 고가용성
  multi_az = var.multi_az

  # 백업 및 복구
  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  copy_tags_to_snapshot   = true
  skip_final_snapshot     = var.skip_final_snapshot
  final_snapshot_identifier_prefix = "${var.identifier}-final-snapshot"

  # 성능 및 모니터링
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  enable_cloudwatch_logs_exports = [
    "postgresql"
  ]

  parameter_group_name = aws_db_parameter_group.postgres.name
  option_group_name    = aws_db_option_group.postgres.name

  # 태그
  tags = merge(
    var.tags,
    {
      Name = var.identifier
    }
  )

  depends_on = [
    aws_db_parameter_group.postgres,
    aws_db_option_group.postgres
  ]
}

# =============================================================================
# KMS 키 (암호화용)
# =============================================================================

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS ${var.identifier}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = var.tags
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.identifier}"
  target_key_id = aws_kms_key.rds.key_id
}

# =============================================================================
# CloudWatch 로그 그룹
# =============================================================================

resource "aws_cloudwatch_log_group" "postgres" {
  name              = "/aws/rds/instance/${var.identifier}/postgresql"
  retention_in_days = 30

  tags = var.tags
}

# =============================================================================
# RDS 연장 모니터링 (선택사항)
# =============================================================================

resource "aws_db_instance_enhanced_monitoring_attributes" "main" {
  count                     = var.enable_enhanced_monitoring ? 1 : 0
  db_instance_identifier    = aws_db_instance.main.identifier
  monitoring_interval       = 60
  monitoring_role_arn       = aws_iam_role.rds_monitoring[0].arn
  enable_iam_database_authentication = true
}

# =============================================================================
# 모니터링 IAM 역할
# =============================================================================

resource "aws_iam_role" "rds_monitoring" {
  count = var.enable_enhanced_monitoring ? 1 : 0
  name  = "${var.identifier}-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count      = var.enable_enhanced_monitoring ? 1 : 0
  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# =============================================================================
# RDS 읽기 전용 복제본 (프로덕션용, 선택사항)
# =============================================================================

resource "aws_db_instance" "read_replica" {
  count = var.enable_read_replica ? 1 : 0

  identifier          = "${var.identifier}-read-replica"
  replicate_source_db = aws_db_instance.main.identifier

  instance_class = var.read_replica_instance_class

  publicly_accessible = false
  skip_final_snapshot = true

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-read-replica"
    }
  )
}

# =============================================================================
# RDS 클러스터 파라미터 그룹 (선택사항)
# =============================================================================

resource "aws_rds_cluster_parameter_group" "postgres" {
  count       = var.enable_cluster_mode ? 1 : 0
  family      = "aurora-postgresql15"
  name        = "${var.identifier}-cluster-params"
  description = "Cluster parameter group for ${var.identifier}"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  tags = var.tags
}

# =============================================================================
# 자동 마이너 버전 업그레이드 정책
# =============================================================================

resource "aws_db_instance_upgrade" "minor_version" {
  db_instance_identifier = aws_db_instance.main.identifier
  auto_minor_version_upgrade = true
}

# =============================================================================
# 스냅샷 복사 (다른 리전으로 재해복구용)
# =============================================================================

resource "aws_db_snapshot_copy" "backup" {
  count = var.enable_snapshot_copy ? 1 : 0

  source_db_snapshot_identifier = aws_db_instance.main.identifier
  target_db_snapshot_identifier = "${var.identifier}-backup"
  source_region                 = var.source_region
}

# =============================================================================
# 메타데이터
# =============================================================================

locals {
  db_connection_string = "postgresql://${var.master_username}@${aws_db_instance.main.endpoint}"
}
