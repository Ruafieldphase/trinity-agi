# Docker 기반 로컬 LLM 스택 가이드

이 문서는 Docker Desktop에서 Ollama `solar:10.7b`와 GGUF 기반 `yanolja/EEVE-Korean-Instruct-10.8B-v1.0` 모델을 동시에 구동하는 방법을 정리한 것입니다.  
기존 PowerShell 스크립트 대신 컨테이너를 활용해 모델을 관리하고, 오케스트레이터에서는 HTTP 엔드포인트만 바꿔서 사용할 수 있습니다.

## 1. 사전 준비
- **Docker Desktop 최신 버전** 및 **WSL2 기반 GPU 패스스루**가 활성화되어 있어야 합니다.  
  - NVIDIA GPU 사용 시 `Settings > Resources > WSL Integration`에서 GPU 지원을 켭니다.
- `docker/Win_LocalLLM` 디렉터리에 이미 내려받은 Ollama 캐시 및 GGUF 모델이 위치합니다.

## 2. 서비스 구성
`docker/Win_LocalLLM/docker-compose.yml`에는 두 개의 서비스가 정의되어 있습니다.

| 서비스 | 포트 | 역할 | 비고 |
|--------|------|------|------|
| `ollama-solar` | `32134` (→ 컨테이너 11434) | Ollama 서버. `solar:10.7b` 등 모델 pull/prompt 실행 | `/root/.ollama`에 기존 캐시를 마운트 |
| `eeve-llamacpp` | `8080` | llama.cpp 기반 HTTP 서버. `EEVE` 모델을 REST API로 제공 | `GET /health`, `POST /completion` 사용 |

두 서비스 모두 `deploy.resources.reservations.devices`로 GPU를 요청합니다. WSL2 + NVIDIA 조합이면 자동으로 GPU를 잡습니다. GPU가 없다면 `deploy` 블록을 주석 처리하거나 `--n-gpu-layers 0` 파라미터로 수정하세요.

## 3. 실행 절차
```powershell
cd docker/Win_LocalLLM
docker compose up -d
```

첫 실행 후 아래 명령으로 Ollama에 한국어 모델을 내려받습니다.
```powershell
docker compose exec ollama-solar ollama pull solar:10.7b
```

### 상태 점검
- Ollama: `curl http://localhost:32134/api/tags`  
- EEVE 서버: `curl http://localhost:8080/health`

### 프롬프트 테스트
```powershell
# Solar
docker compose exec ollama-solar ollama run solar:10.7b "한국어 테스트 문장을 생성해 주세요."

# EEVE
curl -X POST http://localhost:8080/completion `
     -H "Content-Type: application/json" `
     -d '{"prompt":"### Instruction:\n한국어 테스트 문장을 생성해 주세요.\n\n### Response:\n"}'
```

## 4. 오케스트레이터 연결
- `scripts/lmstudio_chat.py` 등 기존 LM Studio HTTP 호출은 `http://localhost:8080`으로 바꿔주면 됩니다.
- Ollama 기반 백엔드는 `http://localhost:32134`를 사용합니다.
- persona 레지스트리 예시:
  ```jsonc
  {
    "backend_id": "local_eeve",
    "type": "http",
    "base_url": "http://localhost:8080",
    "model": "yanolja-eeve",
    "codec": "llamacpp"
  }
  ```

## 5. 중지 및 로그 확인
```powershell
docker compose logs -f eeve-llamacpp
docker compose logs -f ollama-solar
docker compose down
```

## 6. 문제 해결 체크리스트
- **GPU 메모리 부족**: `--n-gpu-layers` 값을 낮추거나 `--threads` 수를 CPU 코어에 맞게 조정.
- **한글 출력이 영어로만 나오는 경우**: 프롬프트에 `Please respond in Korean.` 등 언어 지시를 명시.
- **포트 충돌**: compose 파일의 `11434`, `8080` 포트를 다른 값으로 바꾸고 오케스트레이터 설정도 함께 수정.

이 구성을 통해 Docker Desktop만 켜면 언제든지 한국어 LLM 실험 환경을 재현할 수 있습니다.
