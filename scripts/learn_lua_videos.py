"""
🎬 루아 OBS 녹화 파일 학습
지정된 영상 파일에서 패턴을 추출하고 ARI에 주입
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')

from services.lua_flow_collector import LuaFlowCollector

async def main():
    print('='*60)
    print('🎬 루아 영상 학습')
    print('='*60)
    
    videos = [
        Path(r'C:\workspace\agi\input\obs_recode\2025-12-09 11-45-16.mp4'),
        Path(r'C:\workspace\agi\input\obs_recode\2025-12-08 20-30-39.mp4'),
    ]
    
    collector = LuaFlowCollector()
    
    for v in videos:
        if v.exists():
            size_gb = v.stat().st_size / (1024**3)
            print(f'\n📹 {v.name}: {size_gb:.2f} GB')
            
            if size_gb > 40:
                print('   ⚠️ 매우 큰 파일 - 프레임 추출에 시간이 걸립니다')
            
            print('   🔄 처리 중...')
            result = await collector.process_one(v)
            
            if result:
                print(f'   ✅ 학습 완료!')
            else:
                print(f'   ❌ 처리 실패')
        else:
            print(f'❌ 파일 없음: {v.name}')
    
    print()
    print('🌊 학습 완료!')

if __name__ == "__main__":
    asyncio.run(main())
