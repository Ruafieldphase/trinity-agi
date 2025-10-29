"""
End-to-End (E2E) 테스트 패키지

이 패키지는 ION Mentoring 애플리케이션의 완전한 사용자 여정을 테스트합니다.
E2E 테스트는 전체 시스템이 의도한 대로 작동하는지 검증합니다.

테스트 구조:
- test_complete_user_journeys.py: 18개 핵심 사용자 여정 시나리오

마커:
- @pytest.mark.e2e: E2E 테스트 식별
- @pytest.mark.asyncio: 비동기 테스트

운영:
- 각 배포 전에 모든 E2E 테스트 실행
- 스테이징 환경 배포 후 E2E 스모크 테스트 실행
- 프로덕션 배포 전 완전한 E2E 테스트 실행
"""
