#!/usr/bin/env python3
"""
Rollback Approval Bridge - Lumen v1.4 패턴

승인 연계 브리지: HMAC 서명 링크로 5분 승인 윈도우 제공
"""

import os
import hmac
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 승인 브리지 설정
APPROVAL_SECRET = os.getenv("APPROVAL_SECRET", "lumen-ion-approval-secret-key-2025")
APPROVAL_WINDOW_SECONDS = 300  # 5분
APPROVAL_STATE_FILE = PROJECT_ROOT / "outputs" / "approval_states.json"


class ApprovalStatus(Enum):
    """승인 상태"""
    PENDING = "PENDING"      # 대기 중
    APPROVED = "APPROVED"    # 승인됨
    REJECTED = "REJECTED"    # 거부됨
    EXPIRED = "EXPIRED"      # 만료됨
    EXECUTED = "EXECUTED"    # 실행됨


@dataclass
class ApprovalRequest:
    """승인 요청"""
    request_id: str
    action_type: str  # SCALE_DOWN, ROLLBACK, EMERGENCY_STOP
    reason: str
    details: Dict
    
    created_at: str
    expires_at: str
    
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    hmac_token: Optional[str] = None


class ApprovalBridge:
    """
    Rollback Approval Bridge
    
    Lumen v1.4 패턴: HMAC 서명 링크로 승인 흐름 구현
    """
    
    def __init__(self, secret: str = APPROVAL_SECRET):
        """
        Args:
            secret: HMAC 서명 비밀키
        """
        self.secret = secret.encode('utf-8')
        self.state_file = APPROVAL_STATE_FILE
        self.state_file.parent.mkdir(exist_ok=True)
        
        # 기존 상태 로드
        self.requests: Dict[str, ApprovalRequest] = {}
        self._load_state()
    
    def _generate_hmac_token(self, request_id: str, action_type: str, expires_at: str) -> str:
        """
        HMAC 토큰 생성 (Lumen v1.4 패턴)
        
        Args:
            request_id: 요청 ID
            action_type: 행동 유형
            expires_at: 만료 시각
            
        Returns:
            HMAC 토큰 (hex)
        """
        message = f"{request_id}:{action_type}:{expires_at}".encode('utf-8')
        token = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
        return token
    
    def _verify_hmac_token(self, request_id: str, token: str) -> bool:
        """
        HMAC 토큰 검증
        
        Args:
            request_id: 요청 ID
            token: HMAC 토큰
            
        Returns:
            검증 성공 여부
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        expected_token = self._generate_hmac_token(
            request.request_id,
            request.action_type,
            request.expires_at
        )
        
        return hmac.compare_digest(token, expected_token)
    
    def create_approval_request(
        self,
        action_type: str,
        reason: str,
        details: Dict,
    ) -> ApprovalRequest:
        """
        승인 요청 생성
        
        Args:
            action_type: 행동 유형 (SCALE_DOWN, ROLLBACK, EMERGENCY_STOP)
            reason: 사유
            details: 상세 정보
            
        Returns:
            ApprovalRequest 객체
        """
        now = datetime.utcnow()
        expires = now + timedelta(seconds=APPROVAL_WINDOW_SECONDS)
        
        request_id = f"{action_type.lower()}_{int(now.timestamp())}"
        
        # HMAC 토큰 생성
        hmac_token = self._generate_hmac_token(
            request_id,
            action_type,
            expires.isoformat()
        )
        
        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            reason=reason,
            details=details,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            status=ApprovalStatus.PENDING.value,
            hmac_token=hmac_token,
        )
        
        self.requests[request_id] = request
        self._save_state()
        
        return request
    
    def approve_request(self, request_id: str, token: str, approved_by: str = "system") -> bool:
        """
        승인 요청 승인
        
        Args:
            request_id: 요청 ID
            token: HMAC 토큰
            approved_by: 승인자
            
        Returns:
            승인 성공 여부
        """
        request = self.requests.get(request_id)
        if not request:
            print(f"❌ 요청을 찾을 수 없음: {request_id}")
            return False
        
        # 토큰 검증
        if not self._verify_hmac_token(request_id, token):
            print(f"❌ HMAC 토큰 검증 실패: {request_id}")
            return False
        
        # 만료 확인
        expires_at = datetime.fromisoformat(request.expires_at)
        if datetime.utcnow() > expires_at:
            request.status = ApprovalStatus.EXPIRED.value
            self._save_state()
            print(f"❌ 승인 기간 만료: {request_id}")
            return False
        
        # 승인 처리
        request.status = ApprovalStatus.APPROVED.value
        request.approved_by = approved_by
        request.approved_at = datetime.utcnow().isoformat()
        
        self._save_state()
        
        print(f"✅ 승인 완료: {request_id} by {approved_by}")
        return True
    
    def reject_request(self, request_id: str, token: str) -> bool:
        """
        승인 요청 거부
        
        Args:
            request_id: 요청 ID
            token: HMAC 토큰
            
        Returns:
            거부 성공 여부
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        # 토큰 검증
        if not self._verify_hmac_token(request_id, token):
            return False
        
        request.status = ApprovalStatus.REJECTED.value
        self._save_state()
        
        print(f"❌ 승인 거부: {request_id}")
        return True
    
    def mark_executed(self, request_id: str) -> bool:
        """
        승인 요청 실행 완료 표시
        
        Args:
            request_id: 요청 ID
            
        Returns:
            성공 여부
        """
        request = self.requests.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.APPROVED.value:
            print(f"❌ 승인되지 않은 요청: {request_id}")
            return False
        
        request.status = ApprovalStatus.EXECUTED.value
        self._save_state()
        
        print(f"✅ 실행 완료: {request_id}")
        return True
    
    def get_approval_url(self, request_id: str, base_url: str = "http://localhost:8080") -> str:
        """
        승인 URL 생성 (Slack 링크용)
        
        Args:
            request_id: 요청 ID
            base_url: 베이스 URL
            
        Returns:
            승인 URL
        """
        request = self.requests.get(request_id)
        if not request:
            return ""
        
        return f"{base_url}/api/approve?request_id={request_id}&token={request.hmac_token}"
    
    def get_rejection_url(self, request_id: str, base_url: str = "http://localhost:8080") -> str:
        """
        거부 URL 생성 (Slack 링크용)
        
        Args:
            request_id: 요청 ID
            base_url: 베이스 URL
            
        Returns:
            거부 URL
        """
        request = self.requests.get(request_id)
        if not request:
            return ""
        
        return f"{base_url}/api/reject?request_id={request_id}&token={request.hmac_token}"
    
    def cleanup_expired(self) -> int:
        """
        만료된 요청 정리
        
        Returns:
            정리된 요청 수
        """
        now = datetime.utcnow()
        count = 0
        
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING.value:
                expires_at = datetime.fromisoformat(request.expires_at)
                if now > expires_at:
                    request.status = ApprovalStatus.EXPIRED.value
                    count += 1
        
        if count > 0:
            self._save_state()
        
        return count
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """
        대기 중인 요청 목록
        
        Returns:
            대기 중인 ApprovalRequest 리스트
        """
        self.cleanup_expired()
        
        return [
            req for req in self.requests.values()
            if req.status == ApprovalStatus.PENDING.value
        ]
    
    def _load_state(self):
        """상태 파일 로드"""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for req_dict in data:
                req = ApprovalRequest(**req_dict)
                self.requests[req.request_id] = req
        except Exception as e:
            print(f"⚠️  상태 파일 로드 실패: {e}")
    
    def _save_state(self):
        """상태 파일 저장"""
        try:
            data = [asdict(req) for req in self.requests.values()]
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  상태 파일 저장 실패: {e}")


def main():
    """테스트 함수"""
    print("=" * 70)
    print("Approval Bridge - Lumen v1.4 패턴 테스트")
    print("=" * 70)
    print()
    
    bridge = ApprovalBridge()
    
    # 1. 승인 요청 생성
    print("1️⃣ SCALE_DOWN 승인 요청 생성")
    request = bridge.create_approval_request(
        action_type="SCALE_DOWN",
        reason="Forecasted spend > budget + dissonant rhythm",
        details={
            "current_spend": 25.5,
            "forecasted_spend": 220.0,
            "budget": 200.0,
            "coherence": 0.65,
            "phase": 0.72,
            "entropy": 0.58,
        }
    )
    
    print(f"   Request ID: {request.request_id}")
    print(f"   Status: {request.status}")
    print(f"   Expires: {request.expires_at}")
    if request.hmac_token:
        print(f"   HMAC Token: {request.hmac_token[:20]}...")
    print()
    
    # 2. 승인 URL 생성
    print("2️⃣ 승인/거부 URL 생성")
    approve_url = bridge.get_approval_url(request.request_id)
    reject_url = bridge.get_rejection_url(request.request_id)
    
    print(f"   Approve: {approve_url}")
    print(f"   Reject: {reject_url}")
    print()
    
    # 3. 승인 처리
    print("3️⃣ 승인 요청 승인")
    if request.hmac_token:
        success = bridge.approve_request(
            request.request_id,
            request.hmac_token,
            approved_by="admin@example.com"
        )
        print(f"   Success: {success}")
    print()
    
    # 4. 실행 완료 표시
    print("4️⃣ 실행 완료 표시")
    success = bridge.mark_executed(request.request_id)
    print(f"   Success: {success}")
    print()
    
    # 5. 대기 중인 요청 조회
    print("5️⃣ 대기 중인 요청")
    pending = bridge.get_pending_requests()
    print(f"   Count: {len(pending)}")
    print()
    
    # 6. 상태 파일 확인
    print(f"6️⃣ 상태 파일: {bridge.state_file}")
    if bridge.state_file.exists():
        with open(bridge.state_file, 'r') as f:
            content = f.read()
        print(f"   Size: {len(content)} bytes")
    print()
    
    print("=" * 70)
    print("✅ Approval Bridge 테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
