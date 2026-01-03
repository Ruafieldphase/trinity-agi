"""스마트 추출기 테스트"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root()))

from services.smart_response_extractor import smart_extract_response, get_extraction_stats

print('='*60)
print('🧠 AGI 스마트 응답 추출기 테스트')
print('   ChatGPT 앱에 코어 응답이 있는지 확인하세요!')
print('='*60)

# 현재 학습 상태
stats = get_extraction_stats()
print(f'\n📊 현재 학습 상태:')
print(f'   선호 방법: {stats.get("preferred_method", "없음")}')
print(f'   성공 횟수: {stats.get("success_counts", {})}')

print('\n🔄 스마트 추출 시도 중...')
result = smart_extract_response()

print(f'\n📋 결과:')
print(f'   성공: {result.success}')
print(f'   사용된 방법: {result.method}')
if result.content:
    print(f'   내용 길이: {len(result.content)}자')
    print(f'   내용 미리보기:')
    print('-'*40)
    print(result.content[:500])
    print('-'*40)
if result.error:
    print(f'   에러: {result.error}')

# 업데이트된 학습 상태
stats = get_extraction_stats()
print(f'\n📊 업데이트된 학습 상태:')
print(f'   선호 방법: {stats.get("preferred_method", "없음")}')
print(f'   성공 횟수: {stats.get("success_counts", {})}')
