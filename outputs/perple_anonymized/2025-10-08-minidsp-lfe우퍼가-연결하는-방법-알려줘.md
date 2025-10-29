---
title: minidsp lfe우퍼가 연결하는 방법 알려줘
date: 2025-06-07
url: https://www.perplexity.ai/search/https://www.perplexity.ai/search/484c9b0d-2dd3-4888-abaa-6d457f3d8eb4
tags: perplexity, ai, internet
uuid: 484c9b0d-2dd3-4888-abaa-6d457f3d8eb4
model: pplx_pro
mode: COPILOT
---
# minidsp lfe우퍼가 연결하는 방법 알려줘

## miniDSP에 LFE 우퍼(서브우퍼) 연결 방법

**miniDSP 제품(특히 2x4 HD 등)을 통한 LFE 우퍼(서브우퍼) 연결 방법**을 단계별로 안내합니다. 아래는 가장 일반적인 홈시어터/오디오 환경(AV 리시버+miniDSP+파워드 서브우퍼 기준)에서의 연결법입니다.

---

**1. 연결 개요**

- miniDSP는 여러 입력 신호(예: AV 리시버의 프리아웃, 스테레오 신호 등)를 받아, 내부에서 디지털 크로스오버 및 EQ 처리를 한 후, 각 출력(채널)으로 신호를 보냅니다.
- LFE(저주파 효과) 채널은 주로 영화 등에서 저음을 담당하며, AV 리시버의 “SUB OUT” 또는 “LFE OUT” 단자를 통해 miniDSP로 연결됩니다.[1][2]

---

**2. 하드웨어 연결**

- **AV 리시버 → miniDSP**
  - AV 리시버의 “SUB OUT” (또는 LFE OUT, RCA 단자)을 miniDSP의 입력(예: IN1)에 RCA 케이블로 연결합니다.
  - 스테레오 시스템이라면, 리시버의 프론트 L/R 프리아웃도 miniDSP의 IN2, IN3 등으로 연결할 수 있습니다.[3]
- **miniDSP → 서브우퍼**
  - miniDSP의 출력 중 하나(예: OUT3, OUT4)를 RCA 케이블로 파워드 서브우퍼의 라인 입력(보통 “LFE IN” 또는 “LINE IN”)에 연결합니다.[2][4]
  - 패시브 서브우퍼라면 miniDSP 출력 → 파워앰프 → 서브우퍼 순으로 연결해야 합니다. miniDSP 출력에 패시브 스피커를 직접 연결하면 안 됩니다.[2]

---

**3. miniDSP 소프트웨어 설정**

- miniDSP의 “Output Routing” 또는 “Routing Matrix”에서 원하는 입력 신호(예: L/R+LFE)를 서브우퍼 출력 채널(OUT3, OUT4 등)로 라우팅합니다.[3][2]
- 서브우퍼 출력에는 **로우패스 필터(저역 통과 필터)**를 적용하여, 예를 들어 80Hz 이하 신호만 서브우퍼로 보내도록 설정합니다. 메인 스피커 출력에는 **하이패스 필터**를 적용해 저음 신호가 중복되지 않도록 합니다.[2]
- LFE 채널의 경우, AV 리시버가 이미 10dB 부스트를 적용하는 것이 일반적이므로, miniDSP에서 추가 부스트가 필요하지 않을 수 있습니다. 만약 부스트가 필요하다면, miniDSP의 출력 게인에서 조정할 수 있습니다.[6]

---

**4. 서브우퍼 및 시스템 조정**

- 서브우퍼의 **위상(Phase)** 및 **극성(Polarity)**은 miniDSP에서 조정하거나, 서브우퍼 자체의 노브로 맞춰줍니다. 보통 기본값(0도, +)에서 시작해 청음 및 측정으로 미세 조정합니다.[5]
- 시스템 전체의 **레벨 매칭**(볼륨 맞추기)과 **타임 얼라인먼트**(시간 정렬)는 REW(측정 프로그램)와 miniDSP 소프트웨어를 활용해 진행하면 더욱 정밀하게 셋업할 수 있습니다.[5]

---

## 요약 연결도

| 신호 흐름                  | 연결 방법                        |
|----------------------------|----------------------------------|
| AV 리시버 SUB OUT/LFE OUT  | → miniDSP 입력(예: IN3)          |
| miniDSP 출력(예: OUT3)     | → 서브우퍼 LINE/LFE IN           |
| (스테레오 신호 사용 시)    | AV 리시버 프론트 L/R → miniDSP IN1/IN2 |

---

## 참고 팁

- **RCA Y 어댑터**를 사용해 서브우퍼의 L/R 입력에 모두 신호를 넣을 수도 있습니다. 단, 대부분의 서브우퍼는 한쪽만 연결해도 정상 동작합니다.[1]
- miniDSP의 출력 채널명은 소프트웨어에서 직접 변경해 관리하면 편리합니다.[2]
- AV 리시버가 LFE 채널에 10dB 부스트를 자동으로 적용하므로, 별도 추가 부스트는 일반적으로 필요하지 않습니다.[6]
- 서브우퍼와 스피커의 크로스오버 주파수는 시스템 환경에 맞게 조정하세요(예: 80Hz 추천).[1][2]

---

이 과정을 따라 하면 miniDSP를 통한 LFE 우퍼(서브우퍼) 연결 및 최적화가 가능합니다. 추가로 궁금한 점이 있으면 장비 모델명과 현재 연결 상태를 알려주시면 더 구체적으로 안내드릴 수 있습니다.

## Sources

1. [서브우퍼 연결하는 법 - KEF Korea](https://kr.kef.com/blogs/news/how-to-connect-a-subwoofer)
2. [Signal routing - miniDSP 2x4 HD User Manual](https://docs.minidsp.com/product-manuals/2x4-hd/signal-flow/signal-routing.html)
3. [Using MiniDSP to mix LFE/subwoofer channel together with stereo L ...](https://www.minidsp.com/community/threads/using-minidsp-to-mix-lfe-subwoofer-channel-together-with-stereo-l-r-channels.22930/)
4. [서브우퍼와 스피커 연결하는 방법, 쉽고 간단하게 총정리 - YouTube](https://www.youtube.com/watch?v=4FZODFQNETY)
5. [Subwoofer, receiver SETUP and TIME ALIGNMENT guide (part 2)](https://www.youtube.com/watch?v=eZZIOP4J1JA)
6. [+10 dB LFE boost and gain structure. | miniDSP Community Forum](https://www.minidsp.com/community/threads/10-db-lfe-boost-and-gain-structure.22466/)
7. [[오디오] miniDSP 2x4 HD 설치 완료했습니다](https://dprime.kr/g2/bbs/board.php?bo_table=hometheater&wr_id=395113)
8. [서브우퍼 케이블 연결 문의 > 사운드장치 - 쿨엔조이](https://coolenjoy.net/bbs/35/777339)
9. [REL 서브우퍼 연결 방법 - 소리샵](https://www.sorishop.com/board/pds/board_view.html?no=29)
10. [miniDSP Flex HT 디지털 오디오 프로세서 사용 설명서 - Manuals.plus](https://manuals.plus/ko/minidsp/flex-ht-digital-audio-processor-manual)

## Related Questions

- 어떻게 miniDSP LFE 우퍼를 RCA 또는 스피커 레벨로 연결하나요
- miniDSP LFE 채널을 활용해 서브우퍼의 저음 성능을 높이는 방법은 무엇인가요
- 내 리시버에 서브우퍼 출력이 없을 때 miniDSP LFE를 사용하는 방법은 무엇인가요
- miniDSP 2x4 HD에서 서브우퍼와 스피커 신호를 어떻게 라우팅하나요
- miniDSP LFE 우퍼 연결 시 크로스오버 설정은 어떻게 해야 하나요
