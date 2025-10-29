"""
Running Summary 유지/갱신 유틸리티

모델 호출 없이도 마지막 몇 개 메시지를 기반으로 간단한 러닝 요약을 유지합니다.
요약은 불릿 리스트 형태의 간결한 문장으로 구성되며, 중복 제거와 길이 제한을 적용합니다.
"""

from typing import Dict, List, Optional


def _normalize_line(line: str) -> str:
    """중복 제거를 위한 간단한 정규화"""
    return " ".join((line or "").strip().lower().split())


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def update_running_summary(
    running_summary: Optional[str],
    new_messages: List[Dict[str, str]],
    *,
    max_bullets: int = 8,
    max_chars: int = 800,
    per_line_max: int = 160,
) -> str:
    """
    기존 러닝 요약과 신규 메시지들을 병합하여 슬라이딩 윈도우 요약을 갱신합니다.

    - 불릿 리스트 형태 유지
    - 신규 메시지에서 핵심 1줄 요약 생성 후 추가
    - 중복 제거 및 최근 항목 우선 보존
    - 전체 글자 수 제한 적용

    Args:
        running_summary: 기존 요약(불릿 리스트 문자열)
        new_messages: 최근 메시지 목록 (role: user/assistant, content: str)
        max_bullets: 보존할 최대 불릿 수
        max_chars: 결과 최대 길이(문자)
        per_line_max: 각 불릿 최대 길이(문자)

    Returns:
        갱신된 불릿 리스트 문자열
    """
    # 1) 기존 불릿 파싱
    bullets: List[str] = []
    if running_summary:
        for line in running_summary.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("- "):
                bullets.append(line)
            else:
                bullets.append(f"- {line}")

    # 2) 신규 메시지에서 간단 1줄 요약 생성 (최근 순서 유지)
    for msg in new_messages or []:
        role = (msg.get("role") or "").strip().lower()
        content = (msg.get("content") or "").strip()
        if not content:
            continue

        role_prefix = "U" if role == "user" else ("A" if role == "assistant" else role[:1].upper())
        one_liner = _truncate("{}: {}".format(role_prefix, " ".join(content.split())), per_line_max)
        bullets.append(f"- {one_liner}")

    # 3) 뒤에서부터 중복 제거(최근 항목 우선 유지)
    seen = set()
    deduped_rev: List[str] = []
    for line in reversed(bullets):
        key = _normalize_line(line)
        if key in seen:
            continue
        seen.add(key)
        deduped_rev.append(line)
    deduped = list(reversed(deduped_rev))

    # 4) 최대 불릿 수 제한(뒤에서부터 잘라 최근 유지)
    if len(deduped) > max_bullets:
        deduped = deduped[-max_bullets:]

    # 5) 전체 길이 제한 적용: 초과 시 앞쪽부터 제거(오래된 항목 우선 제거)
    while deduped and sum(len(x) + 1 for x in deduped) > max_chars:  # +1 for newline
        deduped.pop(0)

    return "\n".join(deduped)
