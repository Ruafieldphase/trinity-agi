import importlib.util
import os
import types


def load_module(name: str, rel_path: str) -> types.ModuleType:
    here = os.path.dirname(__file__)
    target = os.path.abspath(os.path.join(here, "..", rel_path))
    spec = importlib.util.spec_from_file_location(name, target)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_vertex_prompt_client_ready_and_send():
    pc_mod = load_module("prompt_client", "prompt_client.py")

    class DummyConnector:
        def __init__(self):
            self.project_id = "p"
            self.location = "l"
            self.model_name = "m"
            self.model = None

        def initialize(self):
            return None

        def load_model(self):
            self.model = object()

        def send_prompt(self, prompt: str) -> str:
            return f"echo:{prompt}"

    c = DummyConnector()
    client = pc_mod.VertexPromptClient(c)
    assert client.ready() is False
    c.load_model()
    assert client.ready() is True
    assert client.send("hi") == "echo:hi"
    info = client.info()
    assert info["project"] == "p" and info["loaded"] is True


def test_create_default_vertex_prompt_client_factory(monkeypatch):
    pc_mod = load_module("prompt_client", "prompt_client.py")
    ion_mod = load_module("ion_first_vertex_ai", "ion_first_vertex_ai.py")

    # Spy on get_runtime_config to ensure it's used
    calls = {"count": 0}

    def fake_get_runtime_config():
        calls["count"] += 1
        return ("p", "l", "m")

    monkeypatch.setattr(ion_mod, "get_runtime_config", fake_get_runtime_config)

    # Monkeypatch loader to return our ion_mod instead of reloading from disk
    def fake_loader():
        return ion_mod

    monkeypatch.setattr(pc_mod, "_load_ion_first_vertex_ai_module", fake_loader)

    client = pc_mod.create_default_vertex_prompt_client()
    assert client is not None
    assert calls["count"] == 1
