import importlib.util
import os
import types

import pytest


def load_module() -> types.ModuleType:
    """Dynamically load ion_first_vertex_ai.py as a module for testing."""
    here = os.path.dirname(__file__)
    target = os.path.abspath(os.path.join(here, "..", "ion_first_vertex_ai.py"))
    spec = importlib.util.spec_from_file_location("ion_first_vertex_ai", target)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader, "Failed to load spec"
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Clear relevant environment variables before each test
    keys = [
        "GOOGLE_CLOUD_PROJECT",
        "GCP_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "GCP_LOCATION",
        "GEMINI_MODEL",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield


def test_get_runtime_config_defaults():
    mod = load_module()
    project, location, model = mod.get_runtime_config()
    assert project == "naeda-genesis"
    assert location == "us-central1"
    assert model == "gemini-1.5-flash-002"


def test_get_runtime_config_env_override(monkeypatch):
    mod = load_module()
    # Set lower-priority keys first, then override with higher-priority ones
    monkeypatch.setenv("GCP_PROJECT", "fallback-project")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "primary-project")
    monkeypatch.setenv("VERTEX_PROJECT_ID", "vertex-project")

    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "fallback-loc")
    monkeypatch.setenv("GCP_LOCATION", "primary-loc")
    monkeypatch.setenv("VERTEX_LOCATION", "vertex-loc")

    monkeypatch.setenv("GEMINI_MODEL", "custom-model")
    monkeypatch.setenv("VERTEX_MODEL", "vertex-model")

    project, location, model = mod.get_runtime_config()
    assert project == "vertex-project"
    assert location == "vertex-loc"
    assert model == "vertex-model"


def test_initialize_import_guard(monkeypatch):
    mod = load_module()
    connector = mod.VertexAIConnector("p", "l", "m")
    # Force import guard path
    monkeypatch.setattr(mod, "vertexai", None)
    with pytest.raises(ImportError):
        connector.initialize()


def test_load_model_import_guard(monkeypatch):
    mod = load_module()
    connector = mod.VertexAIConnector("p", "l", "m")
    # Force import guard path
    monkeypatch.setattr(mod, "GenerativeModel", None)
    with pytest.raises(ImportError):
        connector.load_model()


def test_send_prompt_requires_load():
    mod = load_module()
    connector = mod.VertexAIConnector("p", "l", "m")
    with pytest.raises(RuntimeError):
        connector.send_prompt("hello")


def test_send_prompt_handles_missing_text(monkeypatch):
    mod = load_module()
    connector = mod.VertexAIConnector("p", "l", "m")

    class DummyResponse:
        text = None

    class DummyModel:
        def generate_content(self, prompt: str):
            return DummyResponse()

    # Inject dummy model (no network)
    connector.model = DummyModel()
    out = connector.send_prompt("hi")
    assert out == ""


def test_send_prompt_offline_smoke(monkeypatch):
    """Full send_prompt path with mock model, no network."""
    mod = load_module()
    connector = mod.VertexAIConnector("test-proj", "test-loc", "test-model")

    class MockResponse:
        text = "Mock response from Gemini"

    class MockModel:
        def generate_content(self, prompt: str):
            return MockResponse()

    # Skip actual initialize/load, just inject model
    connector.model = MockModel()
    response = connector.send_prompt("Test prompt")
    assert response == "Mock response from Gemini"
