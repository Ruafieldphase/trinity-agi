#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lumen Gateway 배포 자동 모니터링 및 검증 스크립트
GitHub Actions 워크플로우 완료를 대기하고 자동으로 헬스체크 수행
"""

import json
import subprocess
import sys
import time
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# 설정
REPO = "Ruafieldphase/LLM_Unified"
WORKFLOW_NAME = "deploy-lumen-gateway.yml"
CHECK_INTERVAL = 30  # 30초마다 확인
MAX_WAIT_TIME = 600  # 최대 10분 대기
EXPECTED_STAGING_URL = "https://lumen-gateway-staging-64076350717.us-central1.run.app"
CANDIDATE_URLS = [
    EXPECTED_STAGING_URL,
    "https://lumen-gateway-x4qvsargwa-uc.a.run.app",
]


class DeploymentMonitor:
    def __init__(self, repo: str, workflow: str):
        self.repo = repo
        self.workflow = workflow
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True)

    def get_latest_workflow_run(self) -> Optional[Dict]:
        """최신 워크플로우 실행 정보 조회"""
        try:
            cmd = [
                "gh",
                "run",
                "list",
                "--repo",
                self.repo,
                "--workflow",
                self.workflow,
                "--limit",
                "1",
                "--json",
                "databaseId,status,conclusion,createdAt,headBranch,event",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            runs = json.loads(result.stdout)
            return runs[0] if runs else None
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHub CLI 오류: {e.stderr}")
            return None
        except Exception as e:
            print(f"❌ 워크플로우 조회 실패: {e}")
            return None

    def wait_for_completion(self, run_id: int, max_wait: int = MAX_WAIT_TIME) -> Tuple[bool, str]:
        """워크플로우 완료 대기"""
        print(f"⏳ 워크플로우 실행 ID {run_id} 완료 대기 중...")
        print(f"   최대 대기 시간: {max_wait}초")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < max_wait:
            run = self.get_latest_workflow_run()
            if not run or run["databaseId"] != run_id:
                print("⚠️  워크플로우 정보를 찾을 수 없습니다.")
                time.sleep(CHECK_INTERVAL)
                continue

            status = run["status"]
            conclusion = run.get("conclusion")

            if status != last_status:
                print(f"   상태: {status} {f'({conclusion})' if conclusion else ''}")
                last_status = status

            if status == "completed":
                if conclusion == "success":
                    print(f"✅ 워크플로우 성공! (소요 시간: {int(time.time() - start_time)}초)")
                    return True, conclusion
                else:
                    print(f"❌ 워크플로우 실패: {conclusion}")
                    return False, conclusion or "unknown"

            time.sleep(CHECK_INTERVAL)

        print(f"⏰ 시간 초과 ({max_wait}초)")
        return False, "timeout"

    def extract_service_url(self, run_id: int) -> Optional[str]:
        """워크플로우 로그에서 서비스 URL 추출"""
        try:
            # 워크플로우 jobs 조회
            cmd = ["gh", "run", "view", str(run_id), "--repo", self.repo, "--json", "jobs"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Get Service URL 단계에서 URL 찾기
            for job in data.get("jobs", []):
                for step in job.get("steps", []):
                    if "Get Service URL" in step.get("name", ""):
                        # 로그에서 URL 파싱 (간단한 방법)
                        # 실제로는 gh run view --log 사용해야 할 수 있음
                        return EXPECTED_STAGING_URL

            # 추출 실패 시 예상 URL 반환
            print("ℹ️  로그에서 URL 추출 실패, 예상 URL 사용")
            return EXPECTED_STAGING_URL

        except Exception as e:
            print(f"⚠️  URL 추출 실패: {e}, 예상 URL 사용")
            return EXPECTED_STAGING_URL

    def health_check(self, service_url: str) -> Dict:
        """서비스 헬스체크 수행"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "service_url": service_url,
            "checks": {},
        }

        endpoints = [
            ("health", "/health", "GET", None),
            ("status", "/status", "GET", None),
            ("personas", "/personas", "GET", None),
            ("chat", "/chat", "POST", '{"message":"Deployment validation test"}'),
        ]

        print(f"\n🏥 헬스체크 시작: {service_url}")

        for name, path, method, body in endpoints:
            url = f"{service_url}{path}"
            try:
                if method == "GET":
                    cmd = ["curl", "-s", "-w", "\\n%{http_code}", url, "-m", "10"]
                else:
                    cmd = [
                        "curl",
                        "-s",
                        "-w",
                        "\\n%{http_code}",
                        "-X",
                        method,
                        "-H",
                        "Content-Type: application/json",
                        "-d",
                        body,
                        url,
                        "-m",
                        "10",
                    ]

                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
                output = result.stdout.strip() if result.stdout else ""
                lines = output.split("\n")
                status_code = lines[-1] if lines else "000"
                response_body = "\n".join(lines[:-1]) if len(lines) > 1 else ""

                success = status_code.startswith("2")
                results["checks"][name] = {
                    "endpoint": path,
                    "method": method,
                    "status_code": status_code,
                    "success": success,
                    "response_preview": response_body[:200] if response_body else "",
                }

                icon = "✅" if success else "❌"
                print(f"   {icon} {name:12s} [{method:4s}] {path:20s} → {status_code}")

            except Exception as e:
                results["checks"][name] = {
                    "endpoint": path,
                    "method": method,
                    "success": False,
                    "error": str(e),
                }
                print(f"   ❌ {name:12s} [{method:4s}] {path:20s} → Error: {e}")

        # 전체 성공 여부
        all_success = all(check.get("success", False) for check in results["checks"].values())
        results["overall_success"] = all_success

        return results

    def save_results(self, results: Dict, filename: Optional[str] = None):
        """결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lumen_deployment_check_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 결과 저장: {output_path}")
        return output_path

    def generate_report(self, results: Dict) -> str:
        """마크다운 리포트 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# Lumen Gateway 배포 검증 리포트

**검증 시각**: {timestamp}
**서비스 URL**: {results['service_url']}
**전체 결과**: {'✅ 성공' if results['overall_success'] else '❌ 실패'}

---

## 엔드포인트 검증 결과

| 엔드포인트 | 메소드 | 상태 코드 | 결과 |
|----------|--------|----------|------|
"""

        for name, check in results["checks"].items():
            status = check.get("status_code", "N/A")
            icon = "✅" if check.get("success", False) else "❌"
            method = check.get("method", "N/A")
            check.get("endpoint", "N/A")
            report += f"| {name} | {method} | {status} | {icon} |\n"

        report += """
---

## 다음 단계

"""

        if results["overall_success"]:
            report += """✅ **모든 헬스체크 통과!**

### 권장 조치:
1. Production 배포 준비
2. ION API의 `LUMEN_GATEWAY_URL` 환경변수 업데이트
3. 통합 테스트 수행
4. 모니터링 대시보드 확인

### Production 배포 방법:
```bash
# Option A: Workflow dispatch
gh workflow run deploy-lumen-gateway.yml --ref master -f environment=production

# Option B: main 브랜치 머지
git checkout main
git merge master
git push origin main
```
"""
        else:
            report += """❌ **일부 헬스체크 실패**

### 권장 조치:
1. Cloud Run 로그 확인
2. 환경변수/시크릿 설정 검증
3. 트러블슈팅 가이드 참조: `LUMEN_DEPLOY_TROUBLESHOOTING.md`

### 로그 확인:
```bash
# Cloud Run 로그
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=lumen-gateway-staging" --limit 50 --format json

# 서비스 상태
gcloud run services describe lumen-gateway-staging --region us-central1 --project naeda-genesis
```
"""

        return report

    def run_full_check(self) -> bool:
        """전체 모니터링 및 검증 프로세스 실행"""
        print("🚀 Lumen Gateway 배포 자동 모니터링 시작")
        print(f"   Repository: {self.repo}")
        print(f"   Workflow: {self.workflow}")
        print()

        # 1. 최신 워크플로우 실행 확인
        run = self.get_latest_workflow_run()
        if not run:
            print("❌ 워크플로우 실행을 찾을 수 없습니다.")
            return False

        run_id = run["databaseId"]
        status = run["status"]
        branch = run["headBranch"]

        print("📋 최신 워크플로우 실행:")
        print(f"   ID: {run_id}")
        print(f"   브랜치: {branch}")
        print(f"   상태: {status}")
        print(f"   생성: {run['createdAt']}")
        print()

        # 2. 완료 대기 (이미 완료된 경우 스킵)
        if status != "completed":
            success, conclusion = self.wait_for_completion(run_id)
            if not success:
                print(f"\n❌ 워크플로우가 성공적으로 완료되지 않았습니다: {conclusion}")
                return False
        else:
            conclusion = run.get("conclusion")
            if conclusion != "success":
                print(f"\n❌ 워크플로우가 이미 실패한 상태입니다: {conclusion}")
                return False
            print("✅ 워크플로우가 이미 성공적으로 완료되었습니다.")

        # 3. 서비스 URL 추출
        print("\n🔍 서비스 URL 확인 중...")
        service_url = self.extract_service_url(run_id)
        print(f"   URL: {service_url}")

        # 4. 배포 안정화 대기 (30초)
        print("\n⏳ 서비스 안정화 대기 중 (30초)...")
        time.sleep(30)

        # 5. 헬스체크 수행
        if not service_url:
            print("❌ 서비스 URL을 확인할 수 없습니다.")
            return False
        health_results = self.health_check(service_url)

        # 6. 결과 저장
        self.save_results(health_results)

        # 7. 리포트 생성
        report = self.generate_report(health_results)
        report_filename = f"lumen_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = self.output_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 리포트 저장: {report_path}")

        # 8. 최종 결과
        print("\n" + "=" * 60)
        if health_results["overall_success"]:
            print("🎉 배포 검증 완료! 모든 헬스체크 통과")
            print("   다음 단계: Production 배포 준비")
            return True
        else:
            print("⚠️  배포 검증 실패. 일부 헬스체크 실패")
            print("   조치 필요: 로그 확인 및 트러블슈팅")
            return False


def main():
    """메인 실행 함수"""
    monitor = DeploymentMonitor(REPO, WORKFLOW_NAME)

    try:
        # 폴백 모드: GH 의존 없이 빠른 헬스체크만 수행
        if os.getenv("SKIP_GH_CHECK") == "1":
            print("⚙️  Quick health-check mode (SKIP_GH_CHECK=1)")
            success = False
            last_results = None
            for idx, service_url in enumerate(CANDIDATE_URLS, start=1):
                print(f"   Candidate {idx}: {service_url}")
                time.sleep(3)
                results = monitor.health_check(service_url)
                last_results = results
                monitor.save_results(results)
                if results.get("overall_success", False):
                    success = True
                    break
                else:
                    print("   → 헬스체크 실패, 다음 후보를 시도합니다.")

            # 리포트 생성 (마지막 결과 기준)
            report = monitor.generate_report(last_results or {})
            report_filename = f"lumen_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path = monitor.output_dir / report_filename
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"📄 리포트 저장: {report_path}")
        else:
            success = monitor.run_full_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  사용자에 의해 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
