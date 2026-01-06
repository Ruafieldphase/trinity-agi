#!/usr/bin/env python3
"""
Nightly Consolidation - Hippocampus Long-term Memory Consolidation
매일 새벽에 실행되는 자동 consolidation 작업

작동 방식:
1. Hippocampus 인스턴스 로드
2. 단기 기억 → 장기 기억 변환
3. 결과 저장 및 리포트 생성
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import logging
from workspace_root import get_workspace_root

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 프로젝트 루트 추가
project_root = get_workspace_root()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "fdo_agi_repo"))

def main():
    """메인 실행 함수"""
    try:
        from fdo_agi_repo.copilot.hippocampus import Hippocampus
    except ImportError:
        logger.error("❌ Hippocampus 모듈을 import할 수 없습니다.")
        sys.exit(1)
    
    workspace_root = project_root
    outputs_dir = workspace_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    logger.info("🌙 Nightly Consolidation 시작...")
    logger.info(f"📁 Workspace: {workspace_root}")
    
    # Hippocampus 인스턴스 생성
    try:
        hippo = Hippocampus(workspace_root)
        logger.info("✅ Hippocampus 로드 완료")
    except Exception as e:
        logger.error(f"❌ Hippocampus 로드 실패: {e}")
        sys.exit(1)
    
    # Consolidation 실행
    try:
        logger.info("🧠 Consolidation 실행 중...")
        result = hippo.consolidate(force=False)
        
        logger.info(f"✅ Consolidation 완료:")
        logger.info(f"   - Total: {result.get('total', 0)}")
        logger.info(f"   - Episodic: {result.get('episodic', 0)}")
        logger.info(f"   - Semantic: {result.get('semantic', 0)}")
        logger.info(f"   - Procedural: {result.get('procedural', 0)}")
        
        # 결과 저장
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "consolidation_result": result,
            "status": "success"
        }
        
        # JSON 저장
        result_file = outputs_dir / "consolidation_result_latest.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 결과 저장: {result_file}")
        
        # Markdown 리포트 생성
        report_file = outputs_dir / "consolidation_report_latest.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 🧠 Nightly Consolidation Report\n\n")
            f.write(f"**실행 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 📊 Consolidation 결과\n\n")
            f.write(f"- **Total Consolidated**: {result.get('total', 0)}\n")
            f.write(f"- **Episodic Memories**: {result.get('episodic', 0)}\n")
            f.write(f"- **Semantic Memories**: {result.get('semantic', 0)}\n")
            f.write(f"- **Procedural Memories**: {result.get('procedural', 0)}\n\n")
            f.write(f"## ✅ 상태\n\n")
            f.write(f"- **Status**: Success\n")
            f.write(f"- **Timestamp**: {result_data['timestamp']}\n\n")
            f.write(f"---\n\n")
            f.write(f"*자동 생성: Nightly Consolidation System*\n")
        
        logger.info(f"📄 리포트 생성: {report_file}")
        logger.info("🎉 Nightly Consolidation 완료!")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Consolidation 실패: {e}")
        
        # 에러 저장
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "failed"
        }
        
        error_file = outputs_dir / "consolidation_error_latest.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
