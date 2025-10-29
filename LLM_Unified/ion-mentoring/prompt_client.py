"""
PromptClient abstraction and a thin VertexPromptClient wrapper.

This file is intentionally self-contained and uses dynamic import to access
`ion_first_vertex_ai.py` in the same directory, avoiding package import issues
from the folder name.
"""

from __future__ import annotations

import importlib.util
import os
from abc import ABC, abstractmethod
from typing import Any, Dict


class PromptClient(ABC):
    @abstractmethod
    def ready(self) -> bool:
        """Whether the underlying model is ready to serve requests."""

    @abstractmethod
    def send(self, prompt: str) -> str:
        """Send a prompt and return the response text (may be empty)."""

    @abstractmethod
    def info(self) -> Dict[str, Any]:
        """Return runtime info such as project, location, and model name."""


class VertexPromptClient(PromptClient):
    def __init__(self, connector: Any):
        # connector is expected to expose: project_id, location, model_name,
        # initialize(), load_model(), send_prompt(prompt: str) -> str, and model attr
        self._c = connector

    # Optional convenience chainers
    def initialize(self) -> "VertexPromptClient":
        self._c.initialize()
        return self

    def load(self) -> "VertexPromptClient":
        self._c.load_model()
        return self

    def ready(self) -> bool:
        return getattr(self._c, "model", None) is not None

    def send(self, prompt: str) -> str:
        return self._c.send_prompt(prompt)

    def info(self) -> Dict[str, Any]:
        return {
            "project": getattr(self._c, "project_id", None),
            "location": getattr(self._c, "location", None),
            "model": getattr(self._c, "model_name", None),
            "loaded": self.ready(),
        }


def _load_ion_first_vertex_ai_module():
    here = os.path.dirname(__file__)
    target = os.path.abspath(os.path.join(here, "ion_first_vertex_ai.py"))
    spec = importlib.util.spec_from_file_location("ion_first_vertex_ai", target)
    if not spec or not spec.loader:
        raise RuntimeError("Failed to load ion_first_vertex_ai module spec")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def create_default_vertex_prompt_client() -> VertexPromptClient:
    mod = _load_ion_first_vertex_ai_module()
    project_id, location, model_name = mod.get_runtime_config()
    connector = mod.VertexAIConnector(
        project_id=project_id, location=location, model_name=model_name
    )
    return VertexPromptClient(connector)
