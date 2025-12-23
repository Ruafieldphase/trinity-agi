import logging
import os
import time
from pathlib import Path
import warnings
from typing import Any, Dict, List, Optional, Tuple

# Try importing both SDKs (Vertex AI and AI Studio)
try:
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel as VertexModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

try:
    # google.generativeai는 deprecated 되어 import 시 FutureWarning을 발생시킬 수 있다.
    # "접속 실패"로 오해되는 로그 노이즈를 줄이기 위해 import 구간에서만 경고를 숨긴다.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


RATE_LIMIT_MARKERS = ("429", "rate limit", "quota", "exhausted", "exceeded")


def _load_dotenv_value(name: str) -> str | None:
    """
    Process env에 키가 없더라도, 워크스페이스의 .env에서 값을 읽어올 수 있게 한다.
    - 값을 출력/로그하지 않는다.
    - 기존 env가 있으면 덮어쓰지 않는다.
    """
    try:
        root = Path(__file__).resolve().parents[1]  # C:\workspace\agi
        for env_path in (root / ".env_credentials", root / ".env"):
            if not env_path.exists():
                continue
            text = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in text:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                if k.strip() != name:
                    continue
                val = v.strip().strip('"').strip("'")
                return val or None
    except Exception:
        return None
    return None


class ModelSelector:
    """
    Centralized Gemini model selector.
    Supports both Vertex AI (GCP) and Google AI Studio (API Key).
    """

    def __init__(
        self,
        project: Optional[str] = None,
        location: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("ModelSelector")
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.api_key = os.getenv("GOOGLE_API_KEY") or _load_dotenv_value("GOOGLE_API_KEY")

        # Model preferences (override with env to try Gemini 3.0 / experimental models)
        # Default to generic aliases for maximum compatibility (especially with GenAI/AI Studio)
        self.fast_model = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
        self.balanced_model = os.getenv("GEMINI_BALANCED_MODEL", "gemini-2.5-flash")
        self.vision_model = os.getenv("GEMINI_VISION_MODEL", self.balanced_model)
        self.top_model = (
            os.getenv("GEMINI_TOP_TIER_MODEL")
            or os.getenv("GEMINI_30_MODEL")
            or os.getenv("GEMINI_EXPERIMENTAL_MODEL")
        )

        self.backend = "none" # 'vertex' or 'genai'
        self._cache: Dict[str, Any] = {}
        # Feature flags (avoid repeated 404 calls)
        self.supports_gemini_25_flash = False
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize connection to either GenAI or Vertex AI."""
        # 1. Try GenAI (API Key) first if available - it's often more reliable for personal keys
        if GENAI_AVAILABLE and self.api_key:
            try:
                # Prevent Vertex/GoogleAuth from picking up the Service Account credentials
                # which we know are failing/404ing for this project.
                # Only trust the API Key.
                if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                
                genai.configure(api_key=self.api_key)
                self.backend = "genai"
                self.logger.info(f"Initialized Google AI Studio (GenAI) backend.")
                # Detect whether Gemini 2.5 Flash is available (so we can prefer it without spamming 404s).
                try:
                    names = []
                    for m in genai.list_models():
                        try:
                            if "generateContent" not in getattr(m, "supported_generation_methods", []):
                                continue
                            n = str(getattr(m, "name", "") or "")
                            if n.startswith("models/"):
                                n = n[len("models/") :]
                            if n:
                                names.append(n)
                        except Exception:
                            continue
                    self.supports_gemini_25_flash = any(n.startswith("gemini-2.5-flash") for n in names)
                except Exception:
                    self.supports_gemini_25_flash = False
                return
            except Exception as e:
                self.logger.warning(f"GenAI init failed: {e}")

        # 2. Fallback to Vertex AI
        if VERTEX_AVAILABLE and self.project:
            try:
                vertexai.init(project=self.project, location=self.location)
                self.backend = "vertex"
                self.logger.info(f"Initialized Vertex AI backend ({self.project}/{self.location}).")
                return
            except Exception as e:
                self.logger.error(f"Vertex init failed: {e}")

        self.logger.error("No valid AI backend available (check GOOGLE_API_KEY or Vertex credentials).")

    @property
    def available(self) -> bool:
        return self.backend != "none"

    def _dedup(self, models: List[str]) -> List[str]:
        seen = set()
        ordered = []
        for m in models:
            if not m:
                continue
            if m in seen:
                continue
            seen.add(m)
            ordered.append(m)
        return ordered

    def select_candidates(
        self,
        *,
        intent: str = "",
        text_length: int = 0,
        urgency: bool = False,
        high_precision: bool = False,
        vision: bool = False,
    ) -> List[str]:
        """Return ordered model candidates for this request."""
        candidates: List[str] = []

        # Vision prefers higher fidelity, then balanced.
        if vision:
            if high_precision and self.top_model:
                candidates.append(self.top_model)
            candidates.append(self.vision_model)

        # Complex or long tasks prefer top/balanced.
        if high_precision or text_length > 800 or intent in ["CREATE", "MODIFY", "VERIFY"]:
            if self.top_model:
                candidates.append(self.top_model)
            candidates.append(self.balanced_model)

        # Default path.
        if not candidates:
            if urgency or text_length > 300:
                candidates.append(self.balanced_model)
            else:
                candidates.append(self.fast_model)

        # Fallbacks always available.
        for fallback in (self.balanced_model, self.fast_model):
            if fallback not in candidates:
                candidates.append(fallback)

        ordered = self._dedup(candidates)
        
        # Add version variants for robustness
        extras = []
        for m in ordered:
            if "flash" in m and "002" not in m:
                extras.append(m + "-002") # Try latest 002
                extras.append(m + "-001") # Try older 001
            elif "pro" in m and "002" not in m:
                extras.append(m + "-002")
                extras.append(m + "-001")
        
        full_list = ordered + [e for e in extras if e not in ordered]
        
        # If using GenAI, sometimes "gemini-1.5-flash" (no suffix) is best
        if self.backend == "genai":
            # Prefer Gemini 2.5 Flash when the backend reports it is available.
            if self.supports_gemini_25_flash:
                pref = ["gemini-2.5-flash", "gemini-2.5-flash-002", "gemini-2.5-flash-001"]
                full_list = [p for p in pref if p not in full_list] + full_list
             # Ensure generic names are present for GenAI aliases
            if "gemini-1.5-flash" not in full_list: full_list.append("gemini-1.5-flash")
            if "gemini-1.5-pro" not in full_list: full_list.append("gemini-1.5-pro")

        return self._dedup(full_list)

    def _get_model(self, model_name: str) -> Any:
        if model_name in self._cache:
            return self._cache[model_name]

        model = None
        if self.backend == "genai":
            # AI Studio
            model = genai.GenerativeModel(model_name)
        elif self.backend == "vertex":
            # Vertex AI
            model = VertexModel(model_name)
        
        if model:
            self._cache[model_name] = model
            return model
        raise RuntimeError(f"Cannot get model {model_name}: No backend initialized")

    def generate_content(
        self,
        content: Any,
        *,
        intent: str = "",
        text_length: int = 0,
        urgency: bool = False,
        high_precision: bool = False,
        vision: bool = False,
        generation_config: Optional[dict] = None,
        **kwargs,
    ) -> Tuple[Any, str]:
        """
        Try generation with prioritized models; falls back on quota/rate errors.
        Returns (response, model_used) or raises on total failure.
        """
        if self.backend == "none":
            raise RuntimeError("AI backend not configured")

        candidates = self.select_candidates(
            intent=intent,
            text_length=text_length,
            urgency=urgency,
            high_precision=high_precision,
            vision=vision,
        )

        errors = []
        # stdout print는 운영 로그/대시보드에 노이즈를 만들 수 있어 debug 로깅으로만 남긴다.
        self.logger.debug(f"Candidates: {candidates}")
        for model_name in candidates:
            try:
                print(f"[DEBUG] Trying model: {model_name}")
                model = self._get_model(model_name)
                # Ensure generation_config is compatible (GenAI sometimes strict)
                config = generation_config or {"temperature": 0.35}
                
                response = model.generate_content(
                    content,
                    generation_config=config,
                    **kwargs,
                )
                return response, model_name
            except Exception as e:
                msg = str(e)
                print(f"[DEBUG] Failed {model_name}: {msg}")
                errors.append(f"{model_name}: {msg}")
                lower = msg.lower()
                # Rate limit handling
                if any(marker in lower for marker in RATE_LIMIT_MARKERS):
                    time.sleep(1.2)
                # 404 handling (try next model)
                if "404" in msg or "not found" in lower:
                    continue
                continue

        raise RuntimeError(f"All Gemini candidates failed. Backends: {self.backend}. Last errors: {' | '.join(errors[-3:])}")

    def try_generate_content(self, *args, **kwargs) -> Tuple[Optional[Any], Optional[str]]:
        """Safe wrapper that returns (None, None) on failure."""
        try:
            return self.generate_content(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Model selection failed: {e}")
            return None, None
