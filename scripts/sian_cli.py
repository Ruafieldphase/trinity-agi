#!/usr/bin/env python3
"""
Sian (Gemini CLI) - 메타층 오케스트레이터
간단한 명령줄 인터페이스로 Gemini와 대화
"""
import os
import sys
import argparse
from pathlib import Path

# Import emoji filter
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))
from utils.emoji_filter import remove_emojis

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai 패키지가 필요합니다.")
    print("   설치: pip install google-generativeai")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Sian (Gemini CLI) - 메타층 AI 오케스트레이터")
    parser.add_argument("prompt", nargs="*", help="Gemini에게 보낼 프롬프트")
    parser.add_argument("--model", default="gemini-2.0-flash", 
                       help="사용할 모델 (기본: gemini-2.0-flash)")
    parser.add_argument("--thinking", action="store_true",
                       help="추론 모델 사용 (gemini-2.0-flash-thinking-exp)")
    parser.add_argument("--pro", action="store_true",
                       help="고급 모델 사용 (gemini-2.5-pro)")
    parser.add_argument("--quiet", action="store_true",
                       help="응답만 출력 (메타데이터 숨김)")
    
    args = parser.parse_args()
    
    # API 키 확인
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 프롬프트 구성
    if args.prompt:
        prompt = " ".join(args.prompt)
    else:
        print("💭 프롬프트를 입력하세요 (Ctrl+D로 종료):")
        prompt = sys.stdin.read().strip()
    
    if not prompt:
        print("❌ 프롬프트가 비어있습니다.")
        sys.exit(1)
    
    # 모델 선택
    if args.thinking:
        model_name = "gemini-2.0-flash-thinking-exp"
    elif args.pro:
        model_name = "gemini-2.5-pro"
    else:
        model_name = args.model
    
    # API 호출
    try:
        genai.configure(api_key=api_key)
        
        if not args.quiet:
            print(f"🤖 Sian ({model_name}):")
            print("-" * 60)
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        print(remove_emojis(response.text))
        
        if not args.quiet:
            print("-" * 60)
            print(f"✅ 완료 (모델: {model_name})")
        
    except Exception as e:
        print(f"❌ 오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
