## ✅ RCL 스택 제어 (STOP)

```text
🛑 모든 RCL Job 중지 완료
📡 RCL Stack Status
  Runner Port : 8090
  Bridge Port : 8091
  Tick Hz     : 30
  Feedback Int: 5 sec

⚪ RCLHarmonyRunner → Not running
⚪ RCLSecureBridge → Not running
⚪ RCLFeedbackWorker → Not running

ℹ️  로그 확인: Get-Job -Name <Name> | Receive-Job -Keep

Name                           Value                                                                                   
----                           -----                                                                                   
runner_port                    8090                                                                                    
bridge_port                    8091                                                                                    
tick_hz                        30                                                                                      
feedback_interval              5                                                                                       
jobs                           {System.Collections.Specialized.OrderedDictionary, System.Collections.Specialized.Ord...
```

**Stderr**
```text
(오류 출력 없음)
```

## 🧠 RCL 스택 상태

- Runner Port: `8090`
- Bridge Port: `8091`
- Tick Hz: `30`
- Feedback Interval: `5 sec`

### 프로세스 상태
- ⚪ `RCLHarmonyRunner` → Not running
- ⚪ `RCLSecureBridge` → Not running
- ⚪ `RCLFeedbackWorker` → Not running

```json
{
  "runner_port": 8090,
  "bridge_port": 8091,
  "tick_hz": 30,
  "feedback_interval": 5,
  "jobs": [
    {
      "name": "RCLHarmonyRunner",
      "running": false,
      "state": null,
      "id": null,
      "started": null
    },
    {
      "name": "RCLSecureBridge",
      "running": false,
      "state": null,
      "id": null,
      "started": null
    },
    {
      "name": "RCLFeedbackWorker",
      "running": false,
      "state": null,
      "id": null,
      "started": null
    }
  ]
}
```

