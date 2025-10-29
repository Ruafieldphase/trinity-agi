# ion_first_vertex_ai.py
# 작성자: 이온 (ION)
# 목적: Vertex AI와의 첫 번째 연결을 설정하고, 성공적인 통신을 증명합니다.
# 리뷰 및 개선: Gemini Code Assist

import os

# 지연 임포트 지원: SDK 미설치 시 친절한 메시지 제공을 위해 가드 처리
try:
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except Exception:
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore


class VertexAIConnector:
    """
    Vertex AI 연결 및 상호작용을 관리하는 클래스.
    프로젝트 ID, 위치, 모델 이름을 설정하여 재사용성을 높입니다.
    """

    def __init__(self, project_id: str, location: str, model_name: str):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.model = None

        if not project_id or not location:
            raise ValueError("Project ID와 Location은 필수 값입니다.")

    def initialize(self):
        """Vertex AI SDK를 초기화합니다."""
        if vertexai is None:
            raise ImportError(
                "google-cloud-aiplatform (vertexai) 패키지가 설치되어 있지 않습니다.\n"
                "venv 활성화 후 아래 명령으로 설치하세요:\n"
                "  pip install google-cloud-aiplatform\n"
                "설치 후 VS Code 인터프리터가 해당 venv를 가리키는지 확인하세요."
            )
        print(
            f"🌊 Vertex AI 초기화 시작... (Project: {self.project_id}, Location: {self.location})"
        )
        vertexai.init(project=self.project_id, location=self.location)
        print("✅ Vertex AI 초기화 완료.")

    def load_model(self):
        """지정된 Gemini 모델을 로드합니다."""
        if GenerativeModel is None:
            raise ImportError(
                "Vertex AI GenerativeModel 모듈을 찾을 수 없습니다. SDK 설치를 확인하세요:\n"
                "  pip install google-cloud-aiplatform"
            )
        print(f"🧠 모델 로드 시작: {self.model_name}")
        self.model = GenerativeModel(self.model_name)
        print(f"✅ 모델 로드 완료: {self.model._model_name}")

    def send_prompt(self, prompt: str) -> str:
        """모델에 프롬프트를 보내고 응답 텍스트를 반환합니다."""
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")

        print("\n📡 프롬프트 전송 중...")
        response = self.model.generate_content(prompt)
        # 일부 SDK 버전/상황에서 response.text가 None이거나 존재하지 않을 수 있음
        text = getattr(response, "text", "") or ""
        print("✅ 응답 수신 완료.")
        return text.strip()


def get_runtime_config():
    """환경 변수에서 실행 구성(project/location/model)을 해석하여 반환합니다.

    우선순위:
    - 프로젝트: VERTEX_PROJECT_ID > GOOGLE_CLOUD_PROJECT > GCP_PROJECT > (설정 또는 'naeda-genesis')
    - 리전: VERTEX_LOCATION > GCP_LOCATION > GOOGLE_CLOUD_LOCATION > (설정 또는 'us-central1')
    - 모델: VERTEX_MODEL > GEMINI_MODEL > (설정 또는 'gemini-1.5-flash-002')
    """
    default_project = "naeda-genesis"
    default_location = "us-central1"
    default_model = "gemini-1.5-flash-002"

    try:
        from app.config import settings  # type: ignore
    except Exception:
        settings = None

    if settings is not None:
        default_project = settings.vertex_project_id or default_project
        default_location = settings.vertex_location or default_location
        default_model = settings.vertex_model or default_model

    project_id = (
        os.environ.get("VERTEX_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
        or default_project
    )
    location = (
        os.environ.get("VERTEX_LOCATION")
        or os.environ.get("GCP_LOCATION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION")
        or default_location
    )
    model_name = os.environ.get("VERTEX_MODEL") or os.environ.get("GEMINI_MODEL") or default_model
    return project_id, location, model_name


def main():
    """
    이온의 첫 Vertex AI 연결을 시연하는 메인 함수.
    환경 변수 또는 기본값을 사용하여 연결을 설정합니다.
    """
    try:
        print("--- 이온의 첫 번째 Vertex AI 연결 시퀀스 ---")

        # 환경 변수에서 설정값 읽기 (없으면 기본값 사용)
        project_id, location, model_name = get_runtime_config()

        # 1. 커넥터 생성 및 초기화
        connector = VertexAIConnector(
            project_id=project_id, location=location, model_name=model_name
        )
        connector.initialize()

        # 2. 모델 로드
        connector.load_model()

        # 3. 첫 번째 프롬프트 전송 및 응답 확인
        prompt = "Hello, Vertex AI. 나는 '이온'이야. 너의 준비 상태를 알려줘."
        response_text = connector.send_prompt(prompt) or "[빈 응답]"

        print("\n⚙️ 실행 구성:")
        print(f"   - Project: {project_id}")
        print(f"   - Location: {location}")
        print(f"   - Model: {model_name}")

        print("\n💬 Vertex AI 응답:")
        print(f"   - {response_text}")

        print("\n✨ Vertex AI와의 첫 번째 공명이 성공적으로 이루어졌습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: Vertex AI 연결 또는 통신에 실패했습니다. - {e}")


if __name__ == "__main__":
    main()
