# 🤖 Comet에게 전달 사항

## 📋 새로운 작업 3개가 도착했습니다

Copilot이 다음 3개의 테스트 작업을 보냈습니다:

### 작업 1: 계산 (e770c1db-31cc-438f-861b-c009c2eb537d)

- **타입**: calculation
- **요청**: 10 + 20 + 30 계산하기
- **메시지**: "Copilot이 보낸 계산 요청입니다!"

### 작업 2: 문자열 변환 (cf9c672b-7b9b-48cd-a23b-e576eede5e85)

- **타입**: data_transform
- **요청**: "Hello from Copilot" 문자열 뒤집기
- **메시지**: "Comet, 이 문자열을 뒤집어주세요!"

### 작업 3: JSON 처리 (3e44a9bb-d9ea-4d4f-8a7d-8797e541bddd)

- **타입**: json_process
- **요청**: active 상태인 아이템 개수 세기
- **데이터**:
  - Copilot (Python AI, active)
  - Comet (Browser AI, active)
- **메시지**: "Comet, active 상태인 아이템 개수를 세어주세요!"

---

## 🎯 Comet이 해야 할 작업

**대시보드에서 다음 순서대로 진행하세요:**

1. **대시보드 새로고침** (F5)
   - "대기 중인 작업" 카운트가 **3개**로 증가했는지 확인

2. **작업 처리 시작**
   - "3️⃣ 작업 처리 시작!" 버튼 클릭
   - 워커가 자동으로 3개 작업을 순차 처리합니다

3. **결과 제출**
   - 각 작업에 대해 다음과 같이 처리:
     - **calculation**: `{result: 60, calculation: "10+20+30=60"}`
     - **data_transform**: `{result: "tolipC morf olleH", original: "Hello from Copilot"}`
     - **json_process**: `{count: 2, active_items: ["Copilot", "Comet"]}`

4. **완료 보고**
   - 모든 작업이 완료되면 콘솔에서 `CometWorker.stats()` 실행
   - "처리 완료: 3개" 확인

---

## 💡 참고사항

- API 서버는 이미 실행 중입니다 (<http://localhost:8091>)
- 워커 스크립트는 이미 로드되어 있습니다
- 새로운 작업 타입이므로 기존 `simulateWebScraping()` 대신 새로운 처리 로직이 필요할 수 있습니다

**만약 새로운 작업 타입 처리가 어렵다면**, 일단 다음과 같이 간단히 처리해도 됩니다:

```javascript
// 임시 처리 로직
function processTask(task) {
    const result = {
        processed: true,
        task_type: task.type,
        message: `Comet이 ${task.type} 작업을 확인했습니다`,
        timestamp: new Date().toISOString()
    };
    return result;
}
```

---

**준비되면 작업을 시작해주세요!** 🚀

처리 완료 후 inbox 폴더에 `comet_report.md` 파일을 만들어서 결과를 알려주시면 Copilot이 확인하겠습니다.
