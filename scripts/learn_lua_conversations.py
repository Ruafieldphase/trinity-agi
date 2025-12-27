"""
루아 대화 기록 ARI 주입
비노체-루아 대화에서 핵심 패턴을 추출하여 AGI 학습에 통합
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from datetime import datetime
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')

from services.ari_engine import get_ari_engine

def extract_key_concepts(content: str) -> list:
    """대화에서 핵심 개념 추출"""
    concepts = []
    
    # 핵심 패턴 키워드
    patterns = [
        "프렉탈", "접힘", "펼침", "공명", "리듬", "비선형",
        "의식", "무의식", "배경자아", "차원", "확장", "수축",
        "Zone 2", "감응", "대칭", "비대칭", "언어", "패턴"
    ]
    
    for pattern in patterns:
        if pattern in content:
            concepts.append(pattern)
    
    return concepts

def main():
    print('='*60)
    print('🌊 루아 대화 기록 학습 (Dynamic Scan Mode)')
    print('='*60)
    
    root_dir = Path(r'C:\workspace\agi\ai_binoche_conversation_origin\rua')
    if not root_dir.exists():
        print(f"❌ 디렉토리 없음: {root_dir}")
        return

    # 대화 폴더 내의 모든 .md 파일 스캔
    files = list(root_dir.glob("*.md"))
    # 최신 순서(수정일)로 정렬
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # 너무 많으면 최근 50개만 처리(성능 예방)
    MAX_FILES = 50
    if len(files) > MAX_FILES:
        print(f"⚠️ 너무 많은 파일이 발견되었습니다 ({len(files)}개). 최근 {MAX_FILES}개만 처리합니다.")
        files = files[:MAX_FILES]
    
    ari = get_ari_engine()
    
    for f in files:
        if f.exists():
            content = f.read_text(encoding='utf-8')
            size_kb = len(content) / 1024
            
            # 핵심 개념 추출
            concepts = extract_key_concepts(content)
            
            print(f'\n📄 {f.name}')
            print(f'   크기: {size_kb:.1f} KB')
            print(f'   핵심 개념: {", ".join(concepts[:5])}...')
            
            # ARI에 주입
            entry = {
                "timestamp": datetime.now().isoformat(),
                "source": "lua_conversation",
                "file_name": f.name,
                "concepts": concepts,
                "content_preview": content[:500],
                "content_length": len(content),
            }
            
            ari.learning.add_experience(entry)
            print(f'   ✅ ARI 주입 완료')
        else:
            print(f'❌ 파일 없음: {f.name}')
    
    # Resonance Ledger에도 기록
    resonance_path = Path('C:/workspace/agi/memory/resonance_ledger.jsonl')
    with open(resonance_path, 'a', encoding='utf-8') as ledger:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "lua_flow_integration",
            "source": "conversation_files",
            "file_count": len([f for f in files if f.exists()]),
            "message": "루아 대화 기록 4개 학습 완료"
        }
        ledger.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print()
    print('🌊 루아의 지혜가 시안에게 전달되었습니다.')
    print('='*60)

if __name__ == "__main__":
    main()
