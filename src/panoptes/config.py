"""Validated runtime settings with YAML defaults and environment overrides."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import YamlConfigSettingsSource

from panoptes.errors import ConfigError


class _ConfigGroup(BaseModel):
    """Shared strict settings behavior."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SourcesSettings(_ConfigGroup):
    """Source discovery limits."""

    enabled: bool = True
    concurrency: int = Field(default=10, ge=1, le=500)
    timeout_seconds: float = Field(default=10.0, gt=0, le=300)


class ProbesSettings(_ConfigGroup):
    """Active-probe controls; disabled by default."""

    enabled: bool = False
    concurrency: int = Field(default=3, ge=1, le=100)
    timeout_seconds: float = Field(default=5.0, gt=0, le=120)
    user_agent: str = "PANOPTES/0.1 (+authorized-security-research)"


class BudgetSettings(_ConfigGroup):
    """Per-run resource ceilings."""

    max_requests: int = Field(default=1000, ge=1)
    max_runtime_seconds: int = Field(default=900, ge=1)
    max_concurrency: int = Field(default=20, ge=1, le=1000)
    requests_per_second: float = Field(default=5.0, gt=0, le=1000)


class OutputSettings(_ConfigGroup):
    """Output and persistence preferences."""

    directory: Path = Path("runs")
    format: str = Field(default="json", pattern="^(json|jsonl)$")
    pretty: bool = True


class AlertSettings(_ConfigGroup):
    """Optional notification controls."""

    enabled: bool = False
    webhook_url: str | None = None


class AISettings(_ConfigGroup):
    """Optional AI integration; no external service is required."""

    enabled: bool = False
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None


class MCPSettings(_ConfigGroup):
    """Optional Model Context Protocol integration."""

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)


class Settings(BaseSettings):
    """Top-level settings loaded from panoptes.yaml, then environment."""

    model_config = SettingsConfigDict(
        env_prefix="PANOPTES_",
        env_nested_delimiter="__",
        yaml_file="panoptes.yaml",
        yaml_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )
    sources: SourcesSettings = Field(default_factory=SourcesSettings)
    probes: ProbesSettings = Field(default_factory=ProbesSettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    alert: AlertSettings = Field(default_factory=AlertSettings)
    ai: AISettings = Field(default_factory=AISettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Apply precedence: constructor, environment, YAML, then secrets."""
        del dotenv_settings
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


def load_settings(yaml_path: Path | str | None = None) -> Settings:
    """Load defaults or a specified YAML file; environment values override YAML."""
    try:
        if yaml_path is None:
            return Settings()
        path = Path(yaml_path)
        if not path.is_file():
            raise ConfigError(f"Configuration file does not exist: {path}")

        class _PathSettings(Settings):
            model_config = SettingsConfigDict(
                env_prefix="PANOPTES_",
                env_nested_delimiter="__",
                yaml_file=path,
                yaml_file_encoding="utf-8",
                extra="ignore",
                validate_default=True,
            )

            @classmethod
            def settings_customise_sources(
                cls,
                settings_cls: type[BaseSettings],
                init_settings: PydanticBaseSettingsSource,
                env_settings: PydanticBaseSettingsSource,
                dotenv_settings: PydanticBaseSettingsSource,
                file_secret_settings: PydanticBaseSettingsSource,
            ) -> tuple[PydanticBaseSettingsSource, ...]:
                del dotenv_settings
                return (
                    init_settings,
                    env_settings,
                    YamlConfigSettingsSource(settings_cls, yaml_file=path),
                    file_secret_settings,
                )

        return _PathSettings()
    except ConfigError:
        raise
    except (ValidationError, OSError, ValueError, TypeError) as exc:
        raise ConfigError(f"Unable to load configuration: {exc}") from exc
