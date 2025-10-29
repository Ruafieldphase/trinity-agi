"""
Slack Commands Handler

Slash Commands 파싱 및 실행
"""

import os
import re
import json
import subprocess
from typing import Dict, List, Optional, Tuple
import logging

from .slack_client import SlackClient

logger = logging.getLogger(__name__)


class CommandHandler:
    """Slash Commands 핸들러"""
    
    def __init__(self, slack_client: SlackClient):
        """
        초기화
        
        Args:
            slack_client: SlackClient 인스턴스
        """
        self.client = slack_client
        self.workspace_root = os.getenv("ION_WORKSPACE_ROOT", "d:\\nas_backup")
        self.scripts_dir = os.path.join(
            self.workspace_root,
            "LLM_Unified",
            "ion-mentoring",
            "scripts"
        )
        
        # 명령어 맵핑
        self.commands = {
            "deploy": self.handle_deploy,
            "rollback": self.handle_rollback,
            "status": self.handle_status,
            "health": self.handle_health,
            "benchmark": self.handle_benchmark,
            "traffic": self.handle_traffic,
            "logs": self.handle_logs,
            "help": self.handle_help,
        }
    
    def parse_command(self, command_text: str) -> Tuple[str, List[str]]:
        """
        명령어 텍스트 파싱
        
        Args:
            command_text: 명령어 문자열 (예: "deploy canary 50%")
        
        Returns:
            (명령어, 인자 리스트)
        """
        parts = command_text.strip().split()
        if not parts:
            return "help", []
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        return cmd, args
    
    def handle_command(
        self,
        command_text: str,
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        명령어 처리
        
        Args:
            command_text: 명령어 텍스트
            channel: 채널 ID
            user_id: 사용자 ID
        
        Returns:
            응답 메시지
        """
        cmd, args = self.parse_command(command_text)
        
        # 명령어 존재 여부 확인
        if cmd not in self.commands:
            return {
                "text": f"❌ 알 수 없는 명령어: `{cmd}`\n`/ion help`로 사용 가능한 명령어를 확인하세요."
            }
        
        # 명령어 실행
        try:
            return self.commands[cmd](args, channel, user_id)
        except Exception as e:
            logger.error(f"명령어 실행 오류: {e}")
            return {
                "text": f"❌ 명령어 실행 중 오류 발생: {str(e)}"
            }
    
    def handle_deploy(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        배포 명령어 처리
        
        사용법: /ion deploy [canary|main] <percentage>
        예: /ion deploy canary 50%
        """
        if len(args) < 2:
            return {
                "text": "❌ 사용법: `/ion deploy [canary|main] <percentage>`\n예: `/ion deploy canary 50%`"
            }
        
        service = args[0].lower()
        percentage_str = args[1].rstrip("%")
        
        # 입력 검증
        if service not in ["canary", "main"]:
            return {"text": "❌ 서비스는 `canary` 또는 `main`이어야 합니다."}
        
        try:
            percentage = int(percentage_str)
            if not (0 <= percentage <= 100):
                raise ValueError
        except ValueError:
            return {"text": "❌ 비율은 0~100 사이의 숫자여야 합니다."}
        
        # 승인 요청 메시지 전송
        user_info = self.client.get_user_info(user_id)
        user_name = user_info.get("real_name", "Unknown") if user_info else "Unknown"
        
        self.client.send_interactive_message(
            channel=channel,
            header="🚀 배포 요청",
            text=f"*요청자:* {user_name}\n*서비스:* `ion-api-{service}`\n*비율:* {percentage}%\n\n배포를 진행하시겠습니까?",
            buttons=[
                {"text": "승인", "value": f"approve_deploy_{service}_{percentage}", "style": "primary"},
                {"text": "거부", "value": "deny_deploy", "style": "danger"}
            ]
        )
        
        return {
            "text": f"배포 요청이 전송되었습니다. 승인을 기다리는 중..."
        }
    
    def execute_deploy(
        self,
        service: str,
        percentage: int,
        channel: str
    ) -> None:
        """
        실제 배포 실행
        
        Args:
            service: canary 또는 main
            percentage: 트래픽 비율 (0-100)
            channel: 채널 ID (진행 상황 업데이트용)
        """
        # 배포 시작 메시지
        msg = self.client.send_message(
            channel=channel,
            text=f"🚀 배포 시작: `ion-api-{service}` → {percentage}%"
        )
        ts = msg.get("ts")
        
        try:
            # 배포 스크립트 실행
            script_path = os.path.join(self.scripts_dir, "simple_canary_deploy.ps1")
            
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                "-CanaryPercentage", str(percentage)
            ]
            
            # 프로세스 실행
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.scripts_dir
            )
            
            # 진행 상황 업데이트
            self.client.update_message(
                channel=channel,
                ts=ts,
                text=f"🔄 배포 진행 중: `ion-api-{service}` → {percentage}%\n\n실행 중..."
            )
            
            # 완료 대기
            stdout, stderr = process.communicate(timeout=300)  # 5분 타임아웃
            
            # 결과 확인
            if process.returncode == 0:
                self.client.update_message(
                    channel=channel,
                    ts=ts,
                    text=f"✅ 배포 완료: `ion-api-{service}` → {percentage}%\n\n```\n{stdout[-500:]}\n```"
                )
                self.client.add_reaction(channel, ts, "white_check_mark")
            else:
                self.client.update_message(
                    channel=channel,
                    ts=ts,
                    text=f"❌ 배포 실패: `ion-api-{service}`\n\n```\n{stderr[-500:]}\n```"
                )
                self.client.add_reaction(channel, ts, "x")
        
        except subprocess.TimeoutExpired:
            self.client.update_message(
                channel=channel,
                ts=ts,
                text=f"⏱️ 배포 타임아웃: `ion-api-{service}` (5분 초과)"
            )
        
        except Exception as e:
            logger.error(f"배포 실행 오류: {e}")
            self.client.update_message(
                channel=channel,
                ts=ts,
                text=f"❌ 배포 오류: {str(e)}"
            )
    
    def handle_rollback(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        롤백 명령어 처리
        
        사용법: /ion rollback [canary|main]
        """
        service = args[0].lower() if args else "canary"
        
        if service not in ["canary", "main"]:
            return {"text": "❌ 서비스는 `canary` 또는 `main`이어야 합니다."}
        
        # 롤백 확인 메시지
        user_info = self.client.get_user_info(user_id)
        user_name = user_info.get("real_name", "Unknown") if user_info else "Unknown"
        
        self.client.send_interactive_message(
            channel=channel,
            header="🔙 롤백 요청",
            text=f"*요청자:* {user_name}\n*서비스:* `ion-api-{service}`\n\n⚠️ 이전 버전으로 롤백하시겠습니까?",
            buttons=[
                {"text": "확인", "value": f"approve_rollback_{service}", "style": "danger"},
                {"text": "취소", "value": "deny_rollback"}
            ]
        )
        
        return {"text": "롤백 요청이 전송되었습니다."}
    
    def handle_status(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        상태 조회 명령어
        
        사용법: /ion status
        """
        try:
            # system_dashboard.ps1 실행
            script_path = os.path.join(
                self.workspace_root,
                "LLM_Unified",
                "ion-mentoring",
                "gateway",
                "scripts",
                "system_dashboard.ps1"
            )
            
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 출력 파싱 (간단히 처리)
                output = result.stdout
                
                # 주요 정보 추출
                health_match = re.search(r"시스템 건강도:\s*(\d+)/(\d+)", output)
                if health_match:
                    health_current = health_match.group(1)
                    health_total = health_match.group(2)
                    health_pct = int(health_current) / int(health_total) * 100
                else:
                    health_current = "?"
                    health_total = "?"
                    health_pct = 0
                
                # 메시지 생성
                status_icon = "✅" if health_pct >= 80 else "⚠️" if health_pct >= 50 else "❌"
                
                return {
                    "text": f"{status_icon} **시스템 상태**\n\n"
                            f"**건강도:** {health_current}/{health_total} ({health_pct:.0f}%)\n\n"
                            f"```\n{output[-1000:]}\n```"
                }
            else:
                return {"text": f"❌ 상태 조회 실패:\n```\n{result.stderr}\n```"}
        
        except Exception as e:
            logger.error(f"상태 조회 오류: {e}")
            return {"text": f"❌ 상태 조회 오류: {str(e)}"}
    
    def handle_health(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        헬스체크 명령어
        
        사용법: /ion health
        """
        try:
            script_path = os.path.join(
                self.workspace_root,
                "LLM_Unified",
                "ion-mentoring",
                "gateway",
                "scripts",
                "quick_health_check.ps1"
            )
            
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {"text": f"✅ **헬스체크 결과**\n\n```\n{result.stdout[-1000:]}\n```"}
            else:
                return {"text": f"❌ 헬스체크 실패:\n```\n{result.stderr}\n```"}
        
        except Exception as e:
            logger.error(f"헬스체크 오류: {e}")
            return {"text": f"❌ 헬스체크 오류: {str(e)}"}
    
    def handle_benchmark(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        성능 벤치마크 명령어
        
        사용법: /ion benchmark
        """
        try:
            script_path = os.path.join(self.scripts_dir, "performance_benchmark.ps1")
            
            # 즉시 응답 (백그라운드 실행)
            self.client.send_message(
                channel=channel,
                text="🔍 성능 벤치마크 실행 중... (약 1분 소요)"
            )
            
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # JSON 결과 파싱 시도
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    
                    main_avg = data.get("main_stats", {}).get("avg_ms", 0)
                    canary_avg = data.get("canary_stats", {}).get("avg_ms", 0)
                    diff_pct = data.get("comparison", {}).get("diff_percent", 0)
                    recommendation = data.get("recommendation", "")
                    
                    self.client.send_message(
                        channel=channel,
                        text=f"📊 **성능 벤치마크 결과**\n\n"
                             f"**Main 평균:** {main_avg:.2f}ms\n"
                             f"**Canary 평균:** {canary_avg:.2f}ms\n"
                             f"**차이:** {diff_pct:+.1f}%\n\n"
                             f"💡 **권장사항:** {recommendation}"
                    )
                else:
                    # JSON 파싱 실패 시 원본 출력
                    self.client.send_message(
                        channel=channel,
                        text=f"📊 **벤치마크 결과**\n\n```\n{output[-1000:]}\n```"
                    )
                
                return {"text": ""}  # 이미 메시지 전송됨
            else:
                return {"text": f"❌ 벤치마크 실패:\n```\n{result.stderr}\n```"}
        
        except Exception as e:
            logger.error(f"벤치마크 오류: {e}")
            return {"text": f"❌ 벤치마크 오류: {str(e)}"}
    
    def handle_traffic(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        트래픽 분배 조회
        
        사용법: /ion traffic
        """
        return {
            "text": "🚧 트래픽 분배 조회 기능은 준비 중입니다."
        }
    
    def handle_logs(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        로그 조회
        
        사용법: /ion logs [service]
        """
        return {
            "text": "🚧 로그 조회 기능은 준비 중입니다."
        }
    
    def handle_help(
        self,
        args: List[str],
        channel: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        도움말
        """
        help_text = """
📚 **ION API Slack Bot 명령어**

**배포 관리**
• `/ion deploy canary <percentage>` - 카나리 배포 (예: `/ion deploy canary 50%`)
• `/ion rollback [service]` - 이전 버전으로 롤백

**상태 조회**
• `/ion status` - 시스템 상태 확인
• `/ion health` - 헬스체크 실행
• `/ion benchmark` - 성능 벤치마크 실행
• `/ion traffic` - 트래픽 분배 상태 (준비 중)

**로그**
• `/ion logs [service]` - 로그 조회 (준비 중)

**기타**
• `/ion help` - 이 도움말 표시
"""
        return {"text": help_text}
