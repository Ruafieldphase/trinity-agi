# Failure-to-Learning Compendium v1.0

Naeda 6개월 스프린트 동안 발생했던 대표 실패 사례들을 “감지 → 대응 → 전환” 구조로 정리했습니다. 각 항목은 재현 가능한 로그, 외부 브리지 기록, 익명화된 대화 데이터를 근거로 하고 위치를 함께 표기했습니다. 연구소 협업 시 Tier3 증거 패키지로 바로 편입할 수 있도록 작성했습니다.

## 1. 서문 — 왜 실패 로그를 묶었나
- Rua·Sena 루프 24,138 메시지와 Perple 318건 리서치 브리프를 분석하면서 반복적으로 출현한 `폰트`, `전력`, `플랫폼 쿼터`, `권한` 이슈를 선정했습니다.  
- 모든 기록은 익명화 처리(`outputs/ai_conversations_anonymized.*`)와 공유 패키지 검토(`outputs/share_package_v1/research_package_manifest.csv:1`)를 거쳤습니다.  
- 목적은 **외부 연구소와의 1차 피드백 루프**에서 “현장 실패 → 복구 설계 → 다음 스프린트 액션”을 투명하게 제시하는 것입니다 (`outputs/tier2_slides.md:61`).

## 2. 선언문 폰트 임베딩 실패
**신호**  
- 루멘 선언문 PDF가 기기마다 네모 글리프(□)로 표시되며 사용자가 “콘텐츠가 깨졌다”고 보고 (`outputs/share_package_v1/conversation_samples.md:3`).  
- 상세 진단에서 PDF 생성 도구가 한글 폰트를 포함하지 못했다는 사실을 확인 (`outputs/ChatGPT_언어적_감응_복원.md:5578`).

**대응 흐름**
| 단계 | 실행 내용 | 근거 |
| --- | --- | --- |
| 즉시 진단 | 뷰어가 라틴 기본 폰트(Helvetica)만 포함하도록 빌드되어 한글이 대체 글리프로 렌더링됨을 설명 | `outputs/ChatGPT_언어적_감응_복원.md:5567-5594` |
| 우회 배포 | Noto Sans KR을 내장한 HTML 카드·PDF 재생성, 대비·행간 재조정 | `outputs/ChatGPT_언어적_감응_복원.md:5665-5671` |
| QA 반영 | 다국어 산출물 QA 체크리스트에 “비라틴 문자 표시” 항목 추가 | `outputs/ChatGPT_언어적_감응_복원.md:14348-14354`, `outputs/share_package_v1/conversation_samples.md:13` |

**교훈**
- 다국어 문서는 *항상* 폰트 내장 + 대체 뷰어 안내를 포함한다.  
- 실패 로그를 QA 루틴으로 전환하면 재발 방지가 빠르게 체계화된다.  
- DevContainers 혹은 CICD에서 `fontconfig` 확인 스텝을 미리 배치한다(향후 자동화 추천).

## 3. 인프라 충돌 — 전력 & NAS 경로
**신호**
- 멀티탭 과부하와 팬 속도 저하로 NAS·오디오 장비가 순차적으로 멈춤 (`outputs/share_package_v1/conversation_samples.md:21`).  
- 외부 접근을 위해 QuickConnect, Cloudflare 설정이 반복적으로 실패 (`ai_binoche_conversation_origin/rio/Grok-리오와 비노체의 재회와 대화.md:506-792`).

**대응 흐름**
| 단계 | 실행 내용 | 근거 |
| --- | --- | --- |
| 안전 장비 교체 | Perple 브리지에서 16A 이상, 서지 보호 포함 멀티탭 3종을 2024~2025 후기 데이터로 선별 | `outputs/share_package_v1/conversation_samples.md:24-31` |
| 점검 리듬 도입 | 멀티탭 교체 후 분기별 점검 알림 자동화, NAS/오디오 회로 재배선 | `outputs/share_package_v1/conversation_samples.md:34-36`, `outputs/ai_conversations_anonymized.csv:11935-12007` |
| 원격 접근 보강 | Synology QuickConnect ID, HTTPS 링크, 암호화 스냅샷 생성 절차 문서화 | `ai_binoche_conversation_origin/rio/Grok-리오와 비노체의 재회와 대화.md:570-792` |

**교훈**
- 하드웨어 이슈는 Perple(외부 근거) ↔ Rua/Sena(내부 감응) 루프가 즉시 연결되면 MTTR이 분 단위로 줄어든다.  
- 전력·네트워크 단계에서 “분기 점검 → 로그화 → 공유” 절차를 자동화하여 연구소 환경으로 이식 가능하다.  
- NAS 원격 접근은 암호화 + 권한 분리를 기본값으로, 감응 로그만 공유해도 목적을 달성할 수 있다.

## 4. API / 플랫폼 한계
**신호**
- Vertex AI, Google AI Studio 호출이 간헐적으로 실패하고, API 키 부재·라이브러리 미설치가 혼재 (`outputs/failure_case_vertex_ai_test.py:1-85`).  
- 시스템 모니터는 Vertex AI 마이그레이션을 “PLANNED” 상태로 유지하며 헬스체크에 경고 표시 (`LLM_Unified/system-status.json:1`).

**대응 흐름**
| 단계 | 실행 내용 | 근거 |
| --- | --- | --- |
| 테스트 스크립트 배포 | `failure_case_vertex_ai_test.py`로 API 키 확인, 환경 초기화, 결과 JSON 기록 | `outputs/failure_case_vertex_ai_test.py:19-82` |
| 운영 상태 게시 | `connection_test_results.json`와 `system-status.json` 통합 리뷰, 멘토링 팀 투입 | `outputs/failure_case_vertex_ai_test.py:74-82`, `LLM_Unified/system-status.json:1` |
| 연구 브리프 공유 | Vertex API 쿼터, 대체 경로(Cloud Run, MCP) 설계안을 Tier2/Tier3 문서로 정리 | `outputs/ion_research_brief.md:6-18`, `outputs/tier2_slides.md:18-23` |

**교훈**
- 멀티 에이전트가 의존하는 외부 API는 *항상* 사전 테스트 스크립트와 폴백 경로를 함께 설계한다.  
- 헬스체크 JSON을 주기적으로 공유하면 연구소 파트너가 실시간으로 위험도를 파악할 수 있다.  
- Vertex 이전 단계에서 IAM 권한·Quota Dashboard를 공동으로 리뷰해야 다음 스프린트 일정이 왜곡되지 않는다.

## 5. 워크플로 & 협업 실패
**신호**
- Figma·Canva 렌더링을 자동화하려 했지만, 커넥터 권한과 관리자 승인이 없어서 직접 실행이 차단 (`outputs/ChatGPT_언어적_감응_복원.md:10965-13628`).  
- AI 에이전트가 GitHub·Firebase 등 외부 리소스에 접근하려 할 때 관리자 초대/권한 위임이 미비하여 자동화가 중단 (`outputs/perple_anonymized/2025-10-08-줄스가-naeda-ai-backend-저장소-안에서-...md:123-226`, `outputs/perple_anonymized/2025-10-08-Agent-C-좋은-아침이야.md:1223-1700`).

**대응 흐름**
| 단계 | 실행 내용 | 근거 |
| --- | --- | --- |
| 권한 매트릭스 작성 | 각 플랫폼별(Design, Repo, Cloud) 권한·승인 경로 문서화 | `outputs/perple_anonymized/2025-10-08-줄스가-naeda-ai-backend-저장소-안에서-...md:123-204` |
| 실행 분리 | 설계는 클라우드 대화형 도구가 담당, 실제 실행은 권한이 있는 로컬 Agent S/코멧이 담당하도록 두 계층으로 구분 | `outputs/perple_anonymized/2025-10-08-Agent-C-좋은-아침이야.md:1565-1700` |
| 자동화 명세 제공 | 루멘 선언문 디자인을 Figma/Canva에서 재현할 수 있도록 JSON 스펙·SVG 자산을 패키지화 | `outputs/ChatGPT_언어적_감응_복원.md:13171-14144` |

**교훈**
- “설계 에이전트”와 “실행 에이전트”의 권한 경계를 명확히 하면, 기업 환경에서도 보안 정책을 존중하며 자동화를 이어갈 수 있다.  
- 권한 초대·승인 루틴을 체크리스트로 문서화해야 멀티 에이전트 협업이 중도 차단되지 않는다.  
- 공유 패키지에는 실행에 필요한 최소 자산(SVG, JSON, API Spec)을 포함시켜 재현성을 확보한다.

## 6. 복구 패턴 분석
- 실패는 대부분 **Rua/Sena 감응 루프 → Perple 외부 근거 → 실행 에이전트** 순서로 복구되었다.  
- `outputs/tier2_slides.md:43-55`에서 보듯 메타 마커가 급증한 4~6월에 실패 로그도 집중되었고, 동일 기간에 대응 매뉴얼(폰트 체크, 전력 체크, 권한 매트릭스)이 확립됐다.  
- 세션 토큰 한계가 감지되면 `session_memory_monitor.py`가 경고 이벤트를 남기고, 장기 세션은 자동 분리(`outputs/failure_compendium_draft.md:24-38`) → 로그 인덱싱으로 이어졌다.

## 7. 플레이북 제안
1. **사전 점검**
   - 폰트 내장 여부 테스트 (`outputs/ChatGPT_언어적_감응_복원.md:5586-5594`)
   - 전력·멀티탭 체크리스트 (과부하 차단, 접지, 점검 주기)  
   - Vertex/Gemini API 키, 라이브러리 설치 여부 (`outputs/failure_case_vertex_ai_test.py:24-66`)
2. **실패 감지**
   - Rua/Sena 대화에서 이슈 키워드 트리거 → 자동 태그 (`outputs/concept_occurrences.csv:13580-13600`)  
   - 헬스체크 JSON 모니터링(`LLM_Unified/system-status.json:1`)
3. **복구·보고**
   - 대응 로그를 Markdown + JSON + CSV로 기록하고, `outputs/share_package_v1/research_package_manifest.csv:1`에 등록  
   - 연구소 피드백 루프 전에 Tier2 슬라이드(`outputs/tier2_slides.md:1`)와 1pager(`outputs/agi_research_onepager.md:1`)에 요약 반영

## 부록
| 분류 | 파일 | 비고 |
| --- | --- | --- |
| 익명화 대화 | `outputs/share_package_v1/conversation_samples.md` | 섹션별 대표 대화 |
| 시스템 로그 | `LLM_Unified/system-status.json` | 헬스체크 스냅샷 |
| 테스트 코드 | `outputs/failure_case_vertex_ai_test.py` | API 연결 테스트 |
| 디자인 명세 | `outputs/ChatGPT_언어적_감응_복원.md` | Figma/Canva 재현 자산 |
| 데이터 리포트 | `outputs/ion_research_brief.md`, `outputs/tier2_slides.md` | 연구소 공유용 |

---

**다음 스텝 제안**
1. Tier3 “Failure Compendium”을 이 문서를 베이스로 확장하고, 민감 경로 마스킹 완료 여부를 체크 (`outputs/todo_next_steps.txt:3`).  
2. Docker Desktop Dev Environment에서 QA 루틴을 자동화할 스크립트를 작성해, 다음 스프린트 착수 전에 테스트할 것을 권장합니다.

