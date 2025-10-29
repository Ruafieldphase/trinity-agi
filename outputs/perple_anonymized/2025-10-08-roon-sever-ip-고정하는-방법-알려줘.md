---
title: roon sever ip 고정하는 방법 알려줘
date: 2025-02-19
url: https://www.perplexity.ai/search/https://www.perplexity.ai/search/182ece72-00ec-4acd-af11-bea6f17b63f8
tags: perplexity, ai, internet
uuid: 182ece72-00ec-4acd-af11-bea6f17b63f8
model: turbo
mode: CONCISE
---
# roon sever ip 고정하는 방법 알려줘

Roon 서버의 IP를 고정하려면 아래 단계를 따라 설정할 수 있습니다. 이는 일반적인 네트워크 고정 IP 설정 방법을 기반으로 하며, Roon 서버가 설치된 PC나 장치의 네트워크 설정을 수정하는 방식입니다.

## **1. Roon 서버 장치의 네트워크 정보 확인**
1. **명령 프롬프트 열기**:
   - Windows: 검색창에 `cmd` 입력 후 실행.
   - Mac/Linux: 터미널 실행.
2. `ipconfig /all` (Windows) 또는 `ifconfig` (Mac/Linux)를 입력하여 현재 IPv4 주소, 서브넷 마스크, 기본 게이트웨이 및 DNS 서버 정보를 확인합니다.

## **2. 고정 IP 설정하기**
### **Windows에서 고정 IP 설정**
1. **제어판 열기**:
   - 검색창에 `제어판` 입력 후 실행.
2. **네트워크 및 공유 센터**로 이동:
   - "네트워크 및 인터넷" > "네트워크 및 공유 센터" 선택.
3. **이더넷 또는 Wi-Fi 속성 변경**:
   - 현재 연결된 네트워크를 클릭하고 "속성" 선택.
4. **IPv4 설정 변경**:
   - "인터넷 프로토콜 버전 4(TCP/IPv4)"를 선택하고 "속성" 클릭.
   - "다음 IP 주소 사용"을 선택하고 이전에 확인한 IP 주소, 서브넷 마스크, 게이트웨이 및 DNS 정보를 입력합니다.
5. **확인 후 저장**:
   - 모든 창을 닫고 변경 사항을 저장합니다.

### **IP 공유기를 통한 고정 IP 설정 (예: ipTIME 공유기)**
1. **공유기 관리자 페이지 접속**:
   - 브라우저에서 기본 게이트웨이 주소(예: 192.168.0.1)를 입력하여 접속.
2. **로그인**:
   - 관리자 계정으로 로그인.
3. **DHCP 서버 설정**:
   - "고급 설정" > "네트워크 관리" > "DHCP 서버 설정"으로 이동.
   - Roon 서버 장치의 MAC 주소와 원하는 고정 IP를 입력하고 등록합니다.
4. **저장 후 재부팅**:
   - 설정 저장 후 공유기를 재부팅합니다.[1]

## **3. Roon 서버와 네트워크 연결 확인**
- Roon Core가 설치된 장치에서 네트워크 연결 상태를 확인하고, 고정된 IP로 제대로 작동하는지 테스트합니다.

이 과정을 통해 Roon 서버의 IP를 고정하면, 네트워크 환경에서 안정적인 연결을 유지할 수 있습니다.

## Sources

1. [고정IP 설정 방법 - 사무기기 브랜드파워 1위 현대오피스](https://hd2.co.kr/article/%EA%B7%BC%ED%83%9C%EA%B4%80%EB%A6%AC%EA%B8%B0-%EC%9E%90%EB%A3%8C%EC%8B%A4/2/44888/)
2. [고정 아웃바운드 IP 주소 - Cloud Run](https://cloud.google.com/run/docs/configuring/static-outbound-ip?hl=ko)
3. [[기술자료]Roon 2.0 업데이트, Roon ARC 활용하기 - 네이버 포스트](https://post.naver.com/viewer/postView.naver?volumeNo=34532910&memberNo=6863292)
4. [ROON Setting메뉴구성 알아보기 1편 : General, Storage, Services](https://www.hificlub.co.kr/web2022/board/view.asp?table=brd_10281&pid=16427&brdcat=230)
5. [Roon Server](https://roon.app/ko/core)
6. [뮤직플레이어 Roon 2.0 업데이트, 대박!! 셀룰러 음질 (feat.네트워크 ...](https://blog.naver.com/chardad/222880825152)
7. [Roon ARC](https://roon.app/ko/arc)
8. [Roon 작동 방식](https://roon.app/ko/how-roon-works)

## Related Questions

- Roon 서버의 고정 IP 설정이 네트워크 성능에 미치는 영향은
- Roon 서버의 고정 IP 설정을 변경할 때 주의할 점은
- Roon 서버의 고정 IP 설정을 자동으로 유지하는 방법은
- Roon 서버의 고정 IP 설정을 다른 기기와 공유하는 방법은
- Roon 서버의 고정 IP 설정을 확인하는 가장 빠른 방법은
