#!/bin/bash
# GitHub Actions 서비스 계정에 필요한 IAM 역할 부여

PROJECT_ID="naeda-genesis"
SA_EMAIL="naedacodex-drive-service-accou@naeda-genesis.iam.gserviceaccount.com"

echo "🔧 GitHub Actions 서비스 계정에 IAM 역할 추가 중..."

# 1. Artifact Registry 권한
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.writer" \
  --condition=None

# 2. Cloud Run 권한
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin" \
  --condition=None

# 3. Service Account User (Cloud Run에서 다른 SA 사용 시)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None

# 4. Cloud Build (fallback 배포용)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/cloudbuild.builds.editor" \
  --condition=None

# 5. Storage (Cloud Build 아티팩트용)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.admin" \
  --condition=None

echo "✅ IAM 역할 추가 완료!"
echo ""
echo "📋 부여된 역할:"
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$SA_EMAIL" \
  --format="table(bindings.role)"
