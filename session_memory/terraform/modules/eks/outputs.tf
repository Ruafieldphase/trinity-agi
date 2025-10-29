output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "EKS 클러스터 버전"
  value       = aws_eks_cluster.main.version
}

output "cluster_arn" {
  description = "EKS 클러스터 ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_certificate_authority_data" {
  description = "EKS 클러스터 인증서 데이터"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "cluster_id" {
  description = "EKS 클러스터 ID"
  value       = aws_eks_cluster.main.id
}

output "node_group_id" {
  description = "EKS 노드 그룹 ID"
  value       = aws_eks_node_group.main.id
}

output "node_group_arn" {
  description = "EKS 노드 그룹 ARN"
  value       = aws_eks_node_group.main.arn
}

output "node_role_arn" {
  description = "EKS 노드 역할 ARN"
  value       = aws_iam_role.eks_node_role.arn
}

output "node_security_group_id" {
  description = "EKS 노드 보안 그룹 ID"
  value       = aws_security_group.eks_nodes.id
}
