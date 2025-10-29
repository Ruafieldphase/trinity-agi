# GitHub Actions 서비스 계정에 필요한 IAM 역할 부여 (PowerShell)

$ProjectId = "naeda-genesis"
$ServiceAccountEmail = "naedacodex-drive-service-accou@naeda-genesis.iam.gserviceaccount.com"

Write-Host "🔧 GitHub Actions 서비스 계정에 IAM 역할 추가 중..." -ForegroundColor Cyan

# 1. Artifact Registry 권한
Write-Host "`n1️⃣  Artifact Registry Writer..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/artifactregistry.writer" `
    --condition=None

# 2. Cloud Run 권한
Write-Host "`n2️⃣  Cloud Run Admin..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/run.admin" `
    --condition=None

# 3. Service Account User
Write-Host "`n3️⃣  Service Account User..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/iam.serviceAccountUser" `
    --condition=None

# 4. Cloud Build
Write-Host "`n4️⃣  Cloud Build Editor..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/cloudbuild.builds.editor" `
    --condition=None

# 5. Storage Admin
Write-Host "`n5️⃣  Storage Admin..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/storage.admin" `
    --condition=None

Write-Host "`n✅ IAM 역할 추가 완료!" -ForegroundColor Green
Write-Host "`n📋 부여된 역할:" -ForegroundColor Cyan

gcloud projects get-iam-policy $ProjectId `
    --flatten="bindings[].members" `
    --filter="bindings.members:$ServiceAccountEmail" `
    --format="table(bindings.role)"
