from __future__ import annotations

from pathlib import Path

from aminyx_suggestion_agent.config import resolve_under_backend


class StrategyContentPromptLoader:
    def __init__(self, prompt_path: str) -> None:
        self._path: Path = resolve_under_backend(prompt_path)

    def load(self) -> str:
        if not self._path.is_file():
            raise FileNotFoundError(f"Strategy content system prompt not found: {self._path}")
        return self._path.read_text(encoding="utf-8").strip()
