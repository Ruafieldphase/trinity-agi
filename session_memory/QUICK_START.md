# Quick Start Guide - Agent System 빠른 시작 가이드

## 시스템 실행

### 1. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. API 서버 실행
```bash
python3 agent_api_server.py
```

서버가 `http://localhost:5000`에서 시작됩니다.

### 3. 워크플로우 실행

#### cURL 예제:
```bash
# 워크플로우 실행
curl -X POST http://localhost:5000/api/workflow \
  -H "Content-Type: application/json" \
  -d '{"problem": "데이터 분석 요청"}'

# 응답 예제:
# {
#   "workflow_id": "wf_12345",
#   "status": "pending"
# }

# 상태 조회
curl http://localhost:5000/api/workflow/wf_12345
```

#### Python 예제:
```python
from integrated_agent_system import IntegratedAgentSystem

# 시스템 초기화
system = IntegratedAgentSystem()
system.initialize_agents()

# 워크플로우 실행
result = system.execute_workflow("데이터 분석 요청")

print(f"결과: {result}")
```

---

## 주요 기능 사용법

### 에이전트 직접 사용

#### Sena (분석가)
```python
from agent_sena import SenaAgent
from agent_interface import AgentConfig, AgentRole

config = AgentConfig(
    role=AgentRole.SENA,
    name="Sena",
    description="분석가"
)
sena = SenaAgent(config)
sena.initialize()

# 문제 분석
analysis = sena.perform_analysis("데이터 분석 요청")
print(f"분석 결과: {analysis}")
```

#### Lubit (검증자)
```python
from agent_lubit import LubitAgent

config = AgentConfig(
    role=AgentRole.LUBIT,
    name="Lubit",
    description="게이트키퍼"
)
lubit = LubitAgent(config)
lubit.initialize()

# 분석 검증
analysis_data = {...}  # Sena의 분석 결과
validation = lubit.validate_analysis(analysis_data)
print(f"검증 결과: {validation}")
```

---

## 고급 기능 사용

### 병렬 처리
```python
from parallel_task_system import AdvancedParallelExecutor

executor = AdvancedParallelExecutor(max_workers=4)

# 여러 작업 동시 실행
tasks = [
    lambda: perform_analysis("Task 1"),
    lambda: perform_analysis("Task 2"),
    lambda: perform_analysis("Task 3"),
]

results = executor.execute_workflow(tasks)
print(f"결과: {results}")
```

### 작업 큐 기반 실행
```python
from task_queue_system import TaskQueueManager

manager = TaskQueueManager(num_workers=2)

# 작업 추가
for i in range(10):
    manager.add_task(f"task_{i}", lambda x=i: process_task(x), priority=i%3)

# 모든 작업 완료 대기
manager.wait_until_all_completed(timeout=60)

# 결과 확인
print(f"완료한 작업: {len(manager.results)}")
```

### 캐싱 활용
```python
from caching_system import CachedFunction, Cache

# 함수 캐싱
@CachedFunction(cache=Cache("lru", max_size=1000, ttl=3600))
def expensive_analysis(problem):
    # 비용이 많이 드는 분석 작업
    return perform_analysis(problem)

# 첫 호출: 실제 실행 (시간 소요)
result1 = expensive_analysis("문제1")

# 두 번째 호출: 캐시에서 즉시 반환
result2 = expensive_analysis("문제1")  # 캐시에서 즉시 반환
```

### 에이전트 협력
```python
from agent_collaboration import AgentCollaborationManager

manager = AgentCollaborationManager()

# 에이전트 등록
manager.register_agent("sena", agent_sena)
manager.register_agent("lubit", agent_lubit)
manager.register_agent("gitcode", agent_gitcode)

# 공유 메모리에 정보 저장
manager.collaborative_memory.store(
    key="analysis_result",
    data={"result": "분석 완료"},
    memory_type="SHARED"
)

# 협력 워크플로우 실행
result = manager.execute_collaborative_workflow(
    "data_analysis",
    {"problem": "분석 요청"}
)
```

---

## 모니터링 및 로깅

### 실시간 모니터링
```python
from monitoring_system import HealthCheckManager
from health_check_system import SystemHealthCheck, DatabaseHealthCheck, AgentHealthCheck

manager = HealthCheckManager(check_interval=30)

# 헬스 체크 등록
manager.register_check(SystemHealthCheck("system"))
manager.register_check(DatabaseHealthCheck("database"))
manager.register_check(AgentHealthCheck("sena"))

# 모니터링 시작
manager.start_monitoring()

# 헬스 리포트 생성
report = manager.get_health_report()
print(f"전체 상태: {report['overall_status']}")

# 모니터링 중지
manager.stop_monitoring()
```

### 구조화된 로깅
```python
from logging_system import AgentLogger

logger = AgentLogger(log_dir="logs")

# 에이전트 액션 로깅
logger.log_agent_action(
    agent_id="agent_sena",
    agent_name="Sena",
    action="분석 수행",
    status="완료",
    metadata={"problem": "데이터 분석"}
)

# 메시지 로깅
logger.log_message(
    from_agent="Sena",
    to_agent="Lubit",
    message_type="analysis_submission",
    status="성공",
    metadata={"confidence": 0.92}
)

# 작업 로깅
logger.log_task(
    task_id="task_001",
    task_type="analysis",
    status="완료",
    execution_time=150.5
)
```

---

## 데이터 영속성

### 데이터 저장
```python
from persistence_integration import PersistenceService

persistence = PersistenceService()

# 에이전트 등록
persistence.register_agent("agent_sena", "Sena", "sena", "분석가")

# 워크플로우 생성
wf = persistence.create_workflow(
    description="데이터 분석",
    input_data={"problem": "분석 요청"}
)

# 작업 생성
task = persistence.create_task(
    workflow_id=wf["workflow_id"],
    agent_id="agent_sena",
    description="분석 수행",
    priority=10
)

# 작업 상태 업데이트
persistence.update_task_status(
    task_id=task["task_id"],
    status="completed",
    output_data={"result": "분석 완료"},
    duration_ms=150.5
)

# 메트릭 기록
persistence.update_agent_metrics(
    agent_id="agent_sena",
    total_tasks=10,
    completed_tasks=9,
    success_rate=0.9
)

persistence.close()
```

### 데이터 마이그레이션
```python
from database_migration import MigrationManager

manager = MigrationManager("sqlite:///agent_system.db")

# 현재 상태 확인
manager.status()

# 최신 버전으로 업그레이드
manager.migrate_up()

# 특정 버전으로 이동
manager.migrate_up(target_version=2)

# 다운그레이드
manager.migrate_down(target_version=1)
```

---

## 환경 설정

### 환경별 설정 로드
```python
from config_manager import ConfigManager

# 프로덕션 환경 설정
config = ConfigManager.get_config("production")

# 데이터베이스 설정
print(f"DB URL: {config.database_config.url}")
print(f"Pool Size: {config.database_config.pool_size}")

# 서버 설정
print(f"Server: {config.server_config.host}:{config.server_config.port}")

# 보안 설정
print(f"JWT Secret: {config.security_config.jwt_secret[:10]}...")

# 캐시 설정
print(f"Cache Backend: {config.cache_config.backend}")

# 모니터링 설정
print(f"Health Check Interval: {config.monitoring_config.health_check_interval}s")
```

---

## 환경 변수 설정

### .env 파일 예제
```bash
# 환경
ENVIRONMENT=production

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost/agent_system
DATABASE_POOL_SIZE=20

# 서버
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
SERVER_WORKERS=4

# 캐시
CACHE_BACKEND=redis
CACHE_REDIS_URL=redis://localhost:6379

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=json

# 보안
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION=3600

# 모니터링
HEALTH_CHECK_INTERVAL=30
ALERT_EMAIL=admin@example.com
```

---

## 테스트 실행

### 모든 테스트 실행
```bash
# 통합 테스트
python3 test_integration.py

# 성능 테스트
python3 test_performance.py

# 데이터 영속성 테스트
python3 test_persistence.py
```

### pytest 사용
```bash
# 모든 테스트
pytest

# 특정 테스트 클래스
pytest test_integration.py::TestAgentWorkflow

# 커버리지 리포트
pytest --cov=. --cov-report=html
```

---

## Docker 실행

### 이미지 빌드
```bash
docker build -t agent-system:latest .
```

### 컨테이너 실행
```bash
docker run -d \
  -p 5000:5000 \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://user:pass@db:5432/agent_system \
  --name agent-system \
  agent-system:latest
```

### 헬스 체크
```bash
curl http://localhost:5000/api/health
```

---

## 문제 해결

### 데이터베이스 연결 문제
```python
from persistence_integration import PersistenceService

try:
    persistence = PersistenceService(database_url="sqlite:///test.db")
    persistence.close()
    print("✓ 데이터베이스 연결 성공")
except Exception as e:
    print(f"✗ 연결 실패: {e}")
```

### 에이전트 초기화 문제
```python
from integrated_agent_system import IntegratedAgentSystem

system = IntegratedAgentSystem()
try:
    system.initialize_agents()
    print("✓ 에이전트 초기화 성공")
except Exception as e:
    print(f"✗ 초기화 실패: {e}")
```

### 성능 문제
```python
from parallel_task_system import AdvancedParallelExecutor

# 워커 수 조정
executor = AdvancedParallelExecutor(max_workers=8)

# 캐시 효율성 확인
from caching_system import Cache
cache = Cache("lru", max_size=2000)

# 메트릭 모니터링
from monitoring_system import HealthCheckManager
manager = HealthCheckManager(check_interval=10)
```

---

## 주요 API 엔드포인트

```
POST   /api/workflow              - 워크플로우 실행
GET    /api/workflow/{id}         - 워크플로우 상태 조회
GET    /api/health                - 헬스 체크
GET    /api/metrics               - 시스템 메트릭
GET    /api/agents                - 에이전트 목록
GET    /api/agents/{id}           - 에이전트 상태
POST   /api/agents/{id}/status    - 에이전트 상태 업데이트
```

---

## 유용한 리소스

- **문서**: 각 모듈의 docstring 참조
- **테스트**: test_*.py 파일에서 사용 예제 확인
- **설정**: config_manager.py에서 환경별 설정 확인
- **로그**: logs/ 디렉토리에서 실행 기록 확인

---

## 다음 단계

1. 시스템 시작
2. API를 통해 워크플로우 실행
3. 로그를 통해 실행 과정 확인
4. 모니터링 대시보드 활성화
5. 성능 메트릭 분석

**Happy Running! 🚀**
