#!/usr/bin/env python3
"""
컨텍스트 길이 체크 스크립트
- 토큰 수 계산 (대략적 추정)
- 임계값 경고 (80%, 90%)
- JSON/텍스트 출력
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def estimate_tokens(text: str) -> int:
    """
    토큰 수 대략 추정 (GPT-4 기준)
    - 영어: ~4 chars/token
    - 한글: ~2 chars/token
    - 혼합: ~3 chars/token (보수적)
    """
    # 간단한 휴리스틱: 3 chars = 1 token
    return len(text) // 3


def check_context_length(
    file_path: str,
    max_tokens: int = 128000,
    warn_threshold: float = 0.8,
    critical_threshold: float = 0.9,
    output_json: bool = False
) -> dict:
    """컨텍스트 길이 체크"""
    
    path = Path(file_path)
    if not path.exists():
        return {
            "error": f"파일 없음: {file_path}",
            "file": file_path,
            "timestamp": datetime.now().isoformat()
        }
    
    # 파일 읽기
    content = path.read_text(encoding='utf-8')
    
    # 토큰 수 추정
    estimated_tokens = estimate_tokens(content)
    usage_ratio = estimated_tokens / max_tokens
    
    # 상태 판정
    status = "safe"
    if usage_ratio >= critical_threshold:
        status = "critical"
    elif usage_ratio >= warn_threshold:
        status = "warning"
    
    result = {
        "file": file_path,
        "char_count": len(content),
        "estimated_tokens": estimated_tokens,
        "max_tokens": max_tokens,
        "usage_ratio": round(usage_ratio, 4),
        "usage_percent": round(usage_ratio * 100, 2),
        "status": status,
        "exceeds_threshold": usage_ratio >= warn_threshold,
        "warn_threshold": warn_threshold,
        "critical_threshold": critical_threshold,
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(description="컨텍스트 길이 체크")
    parser.add_argument("--file", required=True, help="체크할 파일 경로")
    parser.add_argument("--max-tokens", type=int, default=128000, help="최대 토큰 수")
    parser.add_argument("--warn-threshold", type=float, default=0.8, help="경고 임계값 (0.8 = 80%)")
    parser.add_argument("--critical-threshold", type=float, default=0.9, help="위험 임계값 (0.9 = 90%)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--out", help="출력 파일 (JSON)")
    
    args = parser.parse_args()
    
    # 체크 실행
    result = check_context_length(
        args.file,
        max_tokens=args.max_tokens,
        warn_threshold=args.warn_threshold,
        critical_threshold=args.critical_threshold,
        output_json=args.json
    )
    
    # 출력
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 텍스트 출력
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        
        print(f"📄 파일: {result['file']}")
        print(f"📊 문자 수: {result['char_count']:,}")
        print(f"🔢 추정 토큰: {result['estimated_tokens']:,} / {result['max_tokens']:,}")
        print(f"📈 사용률: {result['usage_percent']}%")
        print(f"⚡ 상태: {result['status'].upper()}")
        
        if result['status'] == 'critical':
            print(f"\n🚨 위험! {result['critical_threshold']*100}% 초과!")
        elif result['status'] == 'warning':
            print(f"\n⚠️ 경고! {result['warn_threshold']*100}% 초과!")
        else:
            print(f"\n✅ 안전 범위")
    
    # 파일 출력
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        if not args.json:
            print(f"\n💾 저장: {args.out}")
    
    # Exit code
    if result.get('status') == 'critical':
        sys.exit(2)
    elif result.get('status') == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
