"""
A/B 테스트 설정

Lumen Gateway (Treatment) vs Legacy System (Control) 비교
"""

# A/B 테스트 그룹 설정
AB_TEST_CONFIG = {
    "enabled": True,
    "test_name": "lumen_gateway_vs_legacy",
    "start_date": "2025-10-22",
    "end_date": "2025-11-22",  # 1개월 테스트
    # 그룹 설정
    "groups": {
        "control": {
            "name": "legacy",
            "description": "Legacy 추천 시스템 (cf_40_cb_40_pa_20)",
            "percentage": 50,  # 50% 트래픽
            "feature_flags": {"LUMEN_GATEWAY": False},
        },
        "treatment": {
            "name": "lumen_gateway",
            "description": "Lumen Gateway 하이브리드 AI 시스템",
            "percentage": 50,  # 50% 트래픽
            "feature_flags": {"LUMEN_GATEWAY": True},
        },
    },
    # 측정 지표
    "metrics": {
        "primary": {
            "name": "user_satisfaction",
            "description": "사용자 만족도 (1-5점)",
            "target": 4.0,
            "minimum_improvement": 0.1,  # 최소 10% 향상 목표
        },
        "secondary": [
            {
                "name": "response_time",
                "description": "응답 시간 (ms)",
                "target": 10000,  # 10초 이하
                "direction": "lower_is_better",
            },
            {
                "name": "confidence_score",
                "description": "페르소나 선택 신뢰도",
                "target": 0.85,
                "direction": "higher_is_better",
            },
            {
                "name": "persona_accuracy",
                "description": "페르소나 선택 정확도",
                "target": 0.90,
                "direction": "higher_is_better",
            },
        ],
    },
    # 사용자 할당 방식
    "assignment": {
        "method": "hash",  # user_id 해시 기반 안정적 할당
        "seed": 42,
        "sticky": True,  # 동일 사용자는 항상 같은 그룹
    },
    # 통계적 유의성 설정
    "statistics": {
        "confidence_level": 0.95,  # 95% 신뢰 수준
        "minimum_sample_size": 100,  # 그룹당 최소 100명
        "check_interval_days": 7,  # 1주일마다 결과 확인
    },
}


# Canary 배포 설정
CANARY_DEPLOYMENT_CONFIG = {
    "enabled": True,
    "service_name": "ion-api",
    "canary_version": "lumen-gateway-v1",
    # 단계별 트래픽 증가
    "stages": [
        {
            "name": "stage_1",
            "percentage": 5,
            "duration_hours": 24,
            "success_criteria": {
                "error_rate_max": 0.01,  # 1% 이하
                "response_time_p95_max": 15000,  # 15초 이하
                "success_rate_min": 0.95,  # 95% 이상
            },
        },
        {
            "name": "stage_2",
            "percentage": 10,
            "duration_hours": 24,
            "success_criteria": {
                "error_rate_max": 0.01,
                "response_time_p95_max": 15000,
                "success_rate_min": 0.95,
            },
        },
        {
            "name": "stage_3",
            "percentage": 25,
            "duration_hours": 48,
            "success_criteria": {
                "error_rate_max": 0.01,
                "response_time_p95_max": 15000,
                "success_rate_min": 0.95,
            },
        },
        {
            "name": "stage_4",
            "percentage": 50,
            "duration_hours": 72,
            "success_criteria": {
                "error_rate_max": 0.01,
                "response_time_p95_max": 15000,
                "success_rate_min": 0.95,
            },
        },
        {
            "name": "stage_5_full",
            "percentage": 100,
            "duration_hours": None,  # 영구
            "success_criteria": {
                "error_rate_max": 0.01,
                "response_time_p95_max": 15000,
                "success_rate_min": 0.95,
            },
        },
    ],
    # 자동 롤백 조건
    "auto_rollback": {
        "enabled": True,
        "conditions": [
            {
                "metric": "error_rate",
                "threshold": 0.05,  # 5% 초과 시
                "duration_minutes": 5,  # 5분 지속 시
            },
            {
                "metric": "response_time_p95",
                "threshold": 20000,  # 20초 초과 시
                "duration_minutes": 10,
            },
            {"metric": "success_rate", "threshold": 0.90, "duration_minutes": 5},  # 90% 미만 시
        ],
    },
    # 모니터링 설정
    "monitoring": {
        "check_interval_seconds": 60,  # 1분마다 확인
        "alert_channels": ["email", "slack"],
        "dashboard_url": "https://console.cloud.google.com/run",
    },
}


def get_ab_group(user_id: str) -> str:
    """
    사용자 ID 기반 A/B 그룹 할당

    Args:
        user_id: 사용자 ID

    Returns:
        str: 'control' 또는 'treatment'
    """
    import hashlib

    if not AB_TEST_CONFIG["enabled"]:
        return "treatment"  # A/B 테스트 비활성화 시 기본값

    # 사용자 ID 해시 기반 안정적 할당
    seed = AB_TEST_CONFIG["assignment"]["seed"]
    hash_input = f"{user_id}_{seed}".encode("utf-8")
    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)

    # 50/50 할당
    control_percentage = AB_TEST_CONFIG["groups"]["control"]["percentage"]

    if hash_value % 100 < control_percentage:
        return "control"
    else:
        return "treatment"


def should_use_lumen_gateway(user_id: str) -> bool:
    """
    사용자에게 Lumen Gateway를 사용할지 결정

    Args:
        user_id: 사용자 ID

    Returns:
        bool: Lumen Gateway 사용 여부
    """
    ab_group = get_ab_group(user_id)

    if ab_group == "treatment":
        return AB_TEST_CONFIG["groups"]["treatment"]["feature_flags"]["LUMEN_GATEWAY"]
    else:
        return AB_TEST_CONFIG["groups"]["control"]["feature_flags"]["LUMEN_GATEWAY"]


if __name__ == "__main__":
    # 테스트
    print("🧪 A/B 테스트 설정 검증\n")

    # 샘플 사용자 100명으로 분포 확인
    test_users = [f"user_{i}" for i in range(100)]
    control_count = 0
    treatment_count = 0

    for user_id in test_users:
        group = get_ab_group(user_id)
        if group == "control":
            control_count += 1
        else:
            treatment_count += 1

    print("📊 그룹 분포 (N=100):")
    print(f"  • Control (Legacy): {control_count}명 ({control_count}%)")
    print(f"  • Treatment (Lumen): {treatment_count}명 ({treatment_count}%)")

    print("\n✅ A/B 테스트 설정 완료!")
    print("\n📋 Canary 배포 단계:")
    for stage in CANARY_DEPLOYMENT_CONFIG["stages"]:
        print(
            f"  • {stage['name']}: {stage['percentage']}% " f"({stage['duration_hours']}시간)"
            if stage["duration_hours"]
            else f"  • {stage['name']}: {stage['percentage']}% (영구)"
        )
