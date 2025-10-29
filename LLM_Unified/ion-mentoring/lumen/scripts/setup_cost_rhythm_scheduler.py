#!/usr/bin/env python3
"""
Cloud Scheduler 설정 - Cost Rhythm 체크

매시간 Cost Rhythm Loop를 실행하는 Cloud Scheduler Job을 생성합니다.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
REGION = os.getenv("GCP_REGION", "us-central1")
JOB_NAME = "cost-rhythm-hourly-check"
SCHEDULE = "0 * * * *"  # 매시간
TIMEZONE = "UTC"

# Cloud Run 서비스 (Cost Rhythm API)
# TODO: Cost Rhythm API를 Cloud Run으로 배포한 후 활성화
# SERVICE_URL = "https://ion-cost-rhythm-api-...run.app/check"

# 현재는 로컬 스크립트 실행 (Cloud Pub/Sub + Cloud Functions 사용)
PUBSUB_TOPIC = "cost-rhythm-trigger"


def run_command(cmd: str) -> tuple[int, str, str]:
    """명령 실행"""
    print(f"🔧 실행: {cmd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    
    return result.returncode, result.stdout, result.stderr


def create_pubsub_topic() -> bool:
    """Pub/Sub 토픽 생성"""
    print("=" * 70)
    print("1️⃣ Pub/Sub 토픽 생성")
    print("=" * 70)
    
    cmd = (
        f"gcloud pubsub topics create {PUBSUB_TOPIC} "
        f"--project={PROJECT_ID}"
    )
    
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0 or "already exists" in stderr:
        print(f"✅ Pub/Sub 토픽: {PUBSUB_TOPIC}")
        return True
    else:
        print(f"❌ Pub/Sub 토픽 생성 실패: {stderr}")
        return False


def create_scheduler_job() -> bool:
    """Cloud Scheduler Job 생성"""
    print("=" * 70)
    print("2️⃣ Cloud Scheduler Job 생성")
    print("=" * 70)
    
    # Pub/Sub 메시지 페이로드
    payload = json.dumps({
        "action": "cost_rhythm_check",
        "timestamp": "AUTO",
    })
    
    cmd = (
        f"gcloud scheduler jobs create pubsub {JOB_NAME} "
        f"--project={PROJECT_ID} "
        f"--location={REGION} "
        f"--schedule='{SCHEDULE}' "
        f"--time-zone='{TIMEZONE}' "
        f"--topic={PUBSUB_TOPIC} "
        f"--message-body='{payload}' "
        f"--description='Hourly Cost Rhythm Loop check'"
    )
    
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        print(f"✅ Scheduler Job 생성: {JOB_NAME}")
        print(f"   Schedule: {SCHEDULE} ({TIMEZONE})")
        return True
    elif "already exists" in stderr:
        print(f"⚠️  Scheduler Job 이미 존재: {JOB_NAME}")
        
        # 업데이트
        update_cmd = (
            f"gcloud scheduler jobs update pubsub {JOB_NAME} "
            f"--project={PROJECT_ID} "
            f"--location={REGION} "
            f"--schedule='{SCHEDULE}' "
            f"--time-zone='{TIMEZONE}'"
        )
        
        exit_code, stdout, stderr = run_command(update_cmd)
        
        if exit_code == 0:
            print(f"✅ Scheduler Job 업데이트 완료")
            return True
        else:
            print(f"❌ Scheduler Job 업데이트 실패: {stderr}")
            return False
    else:
        print(f"❌ Scheduler Job 생성 실패: {stderr}")
        return False


def list_scheduler_jobs() -> bool:
    """Scheduler Job 목록 조회"""
    print("=" * 70)
    print("3️⃣ Cloud Scheduler Job 목록")
    print("=" * 70)
    
    cmd = (
        f"gcloud scheduler jobs list "
        f"--project={PROJECT_ID} "
        f"--location={REGION}"
    )
    
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        print(stdout)
        return True
    else:
        print(f"❌ 목록 조회 실패: {stderr}")
        return False


def test_scheduler_job() -> bool:
    """Scheduler Job 테스트 실행"""
    print("=" * 70)
    print("4️⃣ Scheduler Job 테스트 실행")
    print("=" * 70)
    
    cmd = (
        f"gcloud scheduler jobs run {JOB_NAME} "
        f"--project={PROJECT_ID} "
        f"--location={REGION}"
    )
    
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        print(f"✅ 테스트 실행 성공")
        print(f"   메시지가 {PUBSUB_TOPIC} 토픽으로 전송되었습니다.")
        return True
    else:
        print(f"❌ 테스트 실행 실패: {stderr}")
        return False


def create_cloud_function_stub():
    """Cloud Function 스텁 생성 가이드"""
    print("=" * 70)
    print("5️⃣ Cloud Function 설정 (TODO)")
    print("=" * 70)
    
    print("""
⚠️  Cloud Function을 생성하여 Pub/Sub 메시지를 처리해야 합니다.

다음 명령으로 Cloud Function을 배포하세요:

```bash
# 1. Cloud Function 디렉토리 생성
mkdir -p cloud_functions/cost_rhythm_trigger

# 2. main.py 작성
cat > cloud_functions/cost_rhythm_trigger/main.py << 'EOF'
import base64
import json
import subprocess

def cost_rhythm_trigger(event, context):
    \"\"\"Pub/Sub 트리거로 Cost Rhythm Loop 실행\"\"\"
    
    # Pub/Sub 메시지 디코딩
    if 'data' in event:
        message = base64.b64decode(event['data']).decode('utf-8')
        print(f"Received message: {message}")
    
    # Cost Rhythm Loop 실행
    # TODO: Cloud Run 서비스 호출 또는 로컬 스크립트 실행
    
    print("Cost Rhythm Loop executed")
    return "OK"
EOF

# 3. requirements.txt 작성
cat > cloud_functions/cost_rhythm_trigger/requirements.txt << 'EOF'
google-cloud-monitoring==2.15.1
google-cloud-storage==2.10.0
EOF

# 4. Cloud Function 배포
gcloud functions deploy cost-rhythm-trigger \\
  --project={PROJECT_ID} \\
  --region={REGION} \\
  --runtime=python311 \\
  --trigger-topic={PUBSUB_TOPIC} \\
  --entry-point=cost_rhythm_trigger \\
  --source=cloud_functions/cost_rhythm_trigger \\
  --timeout=540s \\
  --memory=512MB
```

또는 Cloud Run으로 Cost Rhythm API를 배포하고,
Cloud Scheduler에서 직접 HTTP 호출하는 것을 권장합니다.
""".format(PROJECT_ID=PROJECT_ID, REGION=REGION, PUBSUB_TOPIC=PUBSUB_TOPIC))


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Cloud Scheduler Setup - Cost Rhythm Loop")
    print("=" * 70)
    print()
    
    # 1. Pub/Sub 토픽 생성
    if not create_pubsub_topic():
        print("\n❌ Pub/Sub 토픽 생성 실패")
        return 1
    
    print()
    
    # 2. Scheduler Job 생성
    if not create_scheduler_job():
        print("\n❌ Scheduler Job 생성 실패")
        return 1
    
    print()
    
    # 3. Job 목록 조회
    list_scheduler_jobs()
    
    print()
    
    # 4. 테스트 실행 (선택)
    test = input("🔧 Scheduler Job 테스트 실행하시겠습니까? (y/N): ").strip().lower()
    if test == 'y':
        test_scheduler_job()
    
    print()
    
    # 5. Cloud Function 가이드
    create_cloud_function_stub()
    
    print()
    print("=" * 70)
    print("✅ Cloud Scheduler 설정 완료")
    print("=" * 70)
    print()
    print(f"📋 다음 단계:")
    print(f"1. Cloud Function 또는 Cloud Run API 배포")
    print(f"2. Cost Rhythm Loop를 HTTP 엔드포인트로 노출")
    print(f"3. Scheduler Job이 해당 엔드포인트를 호출하도록 설정")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자 중단")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
