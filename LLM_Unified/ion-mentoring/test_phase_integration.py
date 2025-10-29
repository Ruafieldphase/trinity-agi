"""Phase Registry + PersonaRouter 통합 테스트"""

from persona_phase_registry import PersonaPhaseRegistry
from persona_router import PersonaRouter

print("=" * 60)
print("Phase Registry + PersonaRouter 통합 테스트")
print("=" * 60)

# 테스트 1: PersonaRouter Phase 기능
print("\n[TEST 1] PersonaRouter Phase 기능")
router = PersonaRouter(enable_phases=True)

if router.enable_phases:
    print("✅ Phase Registry 활성화됨")

    # Elro Phase 확인
    elro_phases = router.get_phases_for_persona("Elro")
    print(f"\nElro Phase 개수: {len(elro_phases)}")
    for i, phase in enumerate(elro_phases, 1):
        print(f"  {i}. {phase['name']}")
        print(f"     - {phase['description']}")
else:
    print("⚠️ Phase Registry 비활성화")

# 테스트 2: Phase 프롬프트 주입
print("\n[TEST 2] Phase 프롬프트 주입")
base_prompt = "당신은 Elro입니다. 구조적 설계를 도와주세요."
injected = router.get_phase_prompt("Elro", 0, base_prompt)

print(f"원본 길이: {len(base_prompt)}자")
print(f"주입 후 길이: {len(injected)}자")
print(f"\n주입된 프롬프트 샘플:\n{injected[:400]}...")

# 테스트 3: 모든 Persona Phase 확인
print("\n[TEST 3] 모든 Persona Phase 확인")
for persona in ["Lua", "Elro", "Riri", "Nana"]:
    phases = router.get_phases_for_persona(persona)
    print(f"{persona}: {len(phases)}개 Phase")

# 테스트 4: Lua Phase 2 프롬프트
print("\n[TEST 4] Lua Phase 2 (해결책 제안)")
lua_prompt = router.get_phase_prompt("Lua", 2, "당신은 Lua입니다.")
print(lua_prompt[:300] + "...")

# 테스트 5: 독립 Registry 테스트
print("\n[TEST 5] PersonaPhaseRegistry 독립 테스트")
registry = PersonaPhaseRegistry()
riri_phases = registry.get_phases_for_persona("Riri")
print(f"Riri Phase: {len(riri_phases)}개")
for phase in riri_phases:
    print(f"  - {phase.phase_name}: {len(phase.few_shot_examples)}개 예제")

print("\n✅ Phase Registry 통합 테스트 완료!")
