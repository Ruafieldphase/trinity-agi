# 🤖 Comet Worker 핸들러 확장 가이드

**대상**: VS Code Extension (Comet)  
**목적**: 새로운 작업 타입 처리 능력 추가

---

## 📋 현재 지원되는 작업 타입

| 타입 | 상태 | 설명 |
|-----|------|------|
| `ping` | ✅ 구현됨 | 헬스체크 (pong 응답) |
| `calculation` | ✅ 구현됨 | 단순 계산 (곱셈) |
| `data_transform` | ❌ 미구현 | 텍스트 변환 (대문자/소문자) |
| `batch_calculation` | ❌ 미구현 | 배치 계산 (여러 계산 한 번에) |
| `monitoring_report` | ❌ 미구현 | 모니터링 통계 보고서 |

---

## 🔧 핸들러 구현 방법 (Comet Extension)

### 1️⃣ `data_transform` 핸들러

**위치**: `extension/src/taskHandlers.ts` (또는 유사 파일)

```typescript
async function handleDataTransform(task: Task): Promise<TaskResult> {
  const { operation, text } = task.data;
  
  let result: string;
  
  switch (operation) {
    case 'uppercase':
      result = text.toUpperCase();
      break;
    case 'lowercase':
      result = text.toLowerCase();
      break;
    case 'reverse':
      result = text.split('').reverse().join('');
      break;
    default:
      throw new Error(`Unknown operation: ${operation}`);
  }
  
  return {
    task_id: task.id,
    worker: 'comet-extension',
    status: 'success',
    data: {
      original: text,
      operation: operation,
      result: result
    },
    completed_at: new Date().toISOString()
  };
}
```

---

### 2️⃣ `batch_calculation` 핸들러

```typescript
async function handleBatchCalculation(task: Task): Promise<TaskResult> {
  const { calculations } = task.data;
  const results: Record<string, number> = {};
  
  for (const calc of calculations) {
    const { id, operation, numbers, multiply_by } = calc;
    
    let value: number;
    
    switch (operation) {
      case 'divide':
        value = numbers[0] / numbers[1];
        if (multiply_by) value *= multiply_by;
        break;
      case 'average':
        value = numbers.reduce((a, b) => a + b, 0) / numbers.length;
        break;
      case 'multiply':
        value = numbers.reduce((a, b) => a * b, 1);
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
    
    results[id] = Math.round(value * 100) / 100; // 소수점 2자리
  }
  
  return {
    task_id: task.id,
    worker: 'comet-extension',
    status: 'success',
    data: {
      results: results,
      calculation_count: calculations.length
    },
    completed_at: new Date().toISOString()
  };
}
```

---

### 3️⃣ `monitoring_report` 핸들러

```typescript
import * as fs from 'fs';

async function handleMonitoringReport(task: Task): Promise<TaskResult> {
  const { hours, metrics, ledger_path } = task.data;
  
  // 레저 파일 읽기
  const ledgerData = fs.readFileSync(ledger_path, 'utf-8')
    .split('\n')
    .filter(line => line.trim())
    .map(line => JSON.parse(line));
  
  // 시간 필터링
  const cutoff = new Date();
  cutoff.setHours(cutoff.getHours() - hours);
  
  const recentEvents = ledgerData.filter(event => 
    new Date(event.timestamp) > cutoff
  );
  
  // 메트릭 계산
  const report: Record<string, any> = {
    period_hours: hours,
    total_events: recentEvents.length,
    timestamp: new Date().toISOString()
  };
  
  if (metrics.includes('success_rate')) {
    const success = recentEvents.filter(e => e.status === 'success').length;
    report.success_rate = (success / recentEvents.length * 100).toFixed(1) + '%';
  }
  
  if (metrics.includes('error_count')) {
    report.error_count = recentEvents.filter(e => e.status === 'error').length;
  }
  
  if (metrics.includes('cache_hit_rate')) {
    const cacheHits = recentEvents.filter(e => e.cache_hit === true).length;
    report.cache_hit_rate = (cacheHits / recentEvents.length * 100).toFixed(1) + '%';
  }
  
  return {
    task_id: task.id,
    worker: 'comet-extension',
    status: 'success',
    data: report,
    completed_at: new Date().toISOString()
  };
}
```

---

## 🎯 핸들러 등록

**`extension/src/taskDispatcher.ts`**:

```typescript
export async function handleTask(task: Task): Promise<TaskResult> {
  switch (task.task_type) {
    case 'ping':
      return handlePing(task);
    
    case 'calculation':
      return handleCalculation(task);
    
    case 'data_transform':
      return handleDataTransform(task);  // ✨ 새로 추가
    
    case 'batch_calculation':
      return handleBatchCalculation(task);  // ✨ 새로 추가
    
    case 'monitoring_report':
      return handleMonitoringReport(task);  // ✨ 새로 추가
    
    default:
      throw new Error(`Unknown task type: ${task.task_type}`);
  }
}
```

---

## 🧪 테스트 방법

### 1. 텍스트 변환 테스트

```powershell
cd d:\nas_backup\fdo_agi_repo
.\.venv\Scripts\python.exe scripts\send_text_transform.py
Start-Sleep -Seconds 8
.\.venv\Scripts\python.exe scripts\fetch_and_format_result.py <task_id>
```

**예상 결과**:

```json
{
  "original": "ledger event types: task_completed, error, warning",
  "operation": "uppercase",
  "result": "LEDGER EVENT TYPES: TASK_COMPLETED, ERROR, WARNING"
}
```

---

### 2. 배치 계산 테스트

```powershell
.\.venv\Scripts\python.exe scripts\send_batch_calc.py
Start-Sleep -Seconds 12
.\.venv\Scripts\python.exe scripts\fetch_and_format_result.py <task_id>
```

**예상 결과**:

```json
{
  "results": {
    "success_rate": 84.7,
    "error_rate": 15.3,
    "avg_response": 1.2,
    "cache_hit": 92.3
  },
  "calculation_count": 4
}
```

---

## 📊 구현 우선순위

| 순위 | 핸들러 | 난이도 | 실용성 | 추천 |
|-----|--------|--------|--------|------|
| 1 | `data_transform` | ⭐ 쉬움 | ⭐⭐⭐ 높음 | ✅ 즉시 구현 |
| 2 | `batch_calculation` | ⭐⭐ 중간 | ⭐⭐⭐⭐ 매우 높음 | ✅ 우선 구현 |
| 3 | `monitoring_report` | ⭐⭐⭐ 어려움 | ⭐⭐⭐⭐⭐ 최고 | 🔄 점진적 구현 |

---

## 🚀 다음 단계

1. **Comet Extension에 핸들러 추가**
2. **테스트 실행**
3. **성공 시 문서 업데이트**

핸들러를 구현하면 Copilot ↔ Comet 협업이 더욱 강력해집니다! 🎊
