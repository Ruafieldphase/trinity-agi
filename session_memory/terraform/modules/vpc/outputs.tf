output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "공개 서브넷 IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "프라이빗 서브넷 IDs"
  value       = aws_subnet.private[*].id
}

output "db_subnet_group_name" {
  description = "DB 서브넷 그룹 이름"
  value       = aws_db_subnet_group.main.name
}

output "elasticache_subnet_group_name" {
  description = "ElastiCache 서브넷 그룹 이름"
  value       = aws_elasticache_subnet_group.main.name
}

output "nat_gateway_ips" {
  description = "NAT 게이트웨이 IP"
  value       = var.enable_nat_gateway ? aws_eip.nat[*].public_ip : []
}
