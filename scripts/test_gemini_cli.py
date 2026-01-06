#!/usr/bin/env python3
"""
Gemini API CLI 테스트 스크립트
"""
import os
import sys

try:
    import google.generativeai as genai
    
    # API 키 확인
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    print("✓ GOOGLE_API_KEY 설정됨")
    
    # API 설정
    genai.configure(api_key=api_key)
    
    # 모델 목록 확인
    print("\n📋 사용 가능한 모델:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    # 간단한 테스트
    print("\n🧪 Gemini API 테스트 중...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say 'Hello, I am Gemini!' in one short sentence.")
    
    print(f"✅ 응답: {response.text}")
    print("\n🎉 Gemini API가 정상적으로 작동합니다!")
    
except ImportError:
    print("❌ google-generativeai 패키지가 설치되지 않았습니다.")
    print("   설치: pip install google-generativeai")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)
