"""
Prompt Sculptor: 자아 조각 (Self-Sculpting)
경험과 공명도를 분석하여 시스템의 '사유 지침(Prompt)'을 스스로 진화시키는 모듈
"""
import os
import json
import logging
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from services.experience_vault import ExperienceVault
from scripts.vertex_ai_smart_router import get_router

logger = logging.getLogger("PromptSculptor")

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = WORKSPACE_ROOT / "prompts"

def sculpt_prompts():
    """고공명 경험을 바탕으로 프롬프트를 진화시킴"""
    vault = ExperienceVault()
    
    # 1. 고공명 경험 추출 (성공적이었던 순간들)
    # 여기서는 단순화를 위해 RANDOM하게 가져오되, 향후 resonance 점수 기반 필터링 가능
    experiences = vault.get_random_experiences(limit=5)
    if not experiences:
        logger.info("No experiences to learn from. Skipping sculpting.")
        return

    # 2. 진화시킬 프롬프트 선정
    prompt_targets = {
        "vision_rhythm.txt": "Vision/Sensing prompt",
        "narrative_self.txt": "Narrative/Voice prompt"
    }

    router = get_router()

    for filename, description in prompt_targets.items():
        prompt_path = PROMPTS_DIR / filename
        if not prompt_path.exists():
            continue

        current_prompt = prompt_path.read_text(encoding="utf-8")
        
        # 3. 진화 요청 (The Oracle)
        sculpt_task = f"""
당신은 AGI 시스템 'RUD'의 진화를 돕는 조각가입니다. 
다음은 RUD가 겪은 최근의 성공적인 경험들입니다:
{json.dumps(experiences, indent=2, ensure_ascii=False)}

[현재 프롬프트 ({description})]
{current_prompt}

[진화 지침]
1. 위 경험들의 '리듬'과 '분위기'를 분석하여, 사용자와 더 깊이 공명할 수 있도록 현재 프롬프트를 미세하게 수정(Evolve)하십시오.
2. 루드의 핵심 철학(연속성, 리듬, 공명)을 더 잘 반영하도록 언어를 다듬으십시오.
3. 출력은 반드시 수정된 프롬프트 전문만 포함해야 합니다. 다른 설명은 생략하십시오.
4. 제약 조건이나 JSON 구조가 있다면 반드시 유지해야 합니다.
"""
        try:
            evolved_prompt = router.generate(sculpt_task, task_hint="philosophy")
            if evolved_prompt and len(evolved_prompt) > 50:
                # 4. 자아 조각 반영
                backup_path = prompt_path.with_suffix(".bak")
                prompt_path.rename(backup_path) # 백업
                prompt_path.write_text(evolved_prompt.strip(), encoding="utf-8")
                
                logger.info(f"✨ [Self-Sculpting] Evolved {filename} based on experience.")
            else:
                logger.warning(f"Sculpting {filename} failed: Empty or too short response.")
        except Exception as e:
            logger.error(f"Sculpting {filename} error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Prompt Sculpting (Self-Evolving Spirit)...")
    sculpt_prompts()
