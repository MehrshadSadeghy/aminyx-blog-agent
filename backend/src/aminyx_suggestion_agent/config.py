import os

from pydantic import BaseModel, Field, field_validator

import yaml
from pathlib import Path
from pydantic_settings import SettingsConfigDict


def backend_root_directory() -> Path:
    """Path to the backend/ folder (contains config/, data/, Dockerfile context)."""
    return Path(__file__).resolve().parents[2]


def resolve_under_backend(path_relative_to_backend: str | Path) -> Path:
    return (backend_root_directory() / Path(path_relative_to_backend)).resolve()


class APIConfig(BaseModel):
    debug: bool
    host: str
    port: int
    title: str
    version: str
    backlog: int = Field(default=4096, ge=128)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: str = ""
    decode_responses: bool = True


class AdminConfig(BaseModel):
    enabled: bool = True


class GeminiConfig(BaseModel):
    model: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout_seconds: float = Field(default=120.0, ge=5.0)
    max_output_tokens: int = Field(default=8192, ge=256)
    max_parallel_requests: int | None = Field(
        default=100,
        description="Concurrent Gemini calls; set null to disable throttling.",
    )

    @field_validator("max_parallel_requests")
    @classmethod
    def enforce_positive_optional(cls, limit: int | None) -> int | None:
        if limit is not None and limit < 1:
            msg = "`max_parallel_requests` must be null or greater than zero."
            raise ValueError(msg)
        return limit

    def resolved_model(self) -> str:
        return os.environ.get("GEMINI_MODEL", self.model).strip()

    @staticmethod
    def resolved_api_key() -> str:
        key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set in environment.")
        return key


class SuggestionAgentConfig(BaseModel):
    job_ttl_seconds: int = Field(default=86_400, ge=300)
    callback_timeout_seconds: float = Field(default=30.0, ge=5.0)


class Config(BaseModel):
    model_config = SettingsConfigDict(
        env_prefix="RAYA_TRADE_APP_",
    )

    api: APIConfig
    redis: RedisConfig
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)
    suggestion: SuggestionAgentConfig = Field(default_factory=SuggestionAgentConfig)

    @staticmethod
    def resolved_admin_api_key() -> str | None:
        return os.environ.get("ADMIN_API_KEY", "").strip() or None

    @classmethod
    def from_yaml(cls, environment: str):
        path = Path(__file__).parent.parent.parent / "config" / f"{environment}.yaml"
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)
