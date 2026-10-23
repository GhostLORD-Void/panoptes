"""Tests for P1 core primitives."""
import asyncio
import json
import logging
from pathlib import Path

import orjson
import pytest
import structlog
from pydantic import ValidationError

from panoptes.config import Settings, load_settings
from panoptes.errors import (
    BudgetExceeded,
    ConfigError,
    PanoptesError,
    ProbeError,
    SourceError,
)
from panoptes.events import AssetDiscovered, EventBus, RunStarted
from panoptes.logging import bind_run_context, clear_run_context, configure_logging
from panoptes.models import (
    Asset,
    AssetType,
    Edge,
    EdgeType,
    Finding,
    FindingSeverity,
    Provenance,
    RunResult,
)


def test_models_validate_serialize_and_freeze() -> None:
    provenance = Provenance(source="dns", reference="example.test")
    asset = Asset(
        id="a1",
        value="example.test",
        type=AssetType.DOMAIN,
        tags=("root",),
        provenance=(provenance,),
    )
    payload = orjson.loads(asset.to_json())
    assert payload["type"] == "domain"
    assert payload["provenance"][0]["source"] == "dns"
    with pytest.raises(ValidationError):
        asset.value = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Asset(id="", value="x")
    with pytest.raises(ValidationError):
        Asset(id="a", value="x", confidence=2)


def test_edge_finding_and_run_result_json() -> None:
    edge = Edge(id="e1", source="a", target="b", type=EdgeType.HOSTS)
    finding = Finding(
        id="f1",
        title="Interesting service",
        source="probe",
        severity=FindingSeverity.MEDIUM,
        asset_ids=("a",),
    )
    run = RunResult(run_id="r1", target="example.test", findings=(finding,))
    assert json.loads(edge.to_json())["type"] == "hosts"
    assert json.loads(finding.to_json())["severity"] == "medium"
    assert json.loads(run.to_json())["findings"][0]["id"] == "f1"
    with pytest.raises(ValidationError):
        Edge(id="e", source="a", target="b", type="not-a-type")


def test_settings_defaults_and_validation() -> None:
    settings = Settings()
    assert settings.probes.enabled is False
    assert settings.budget.max_requests == 1000
    assert settings.sources.concurrency > 0
    with pytest.raises(ValidationError):
        Settings(budget={"max_requests": 0})


def test_yaml_settings_and_environment_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text(
        "budget:\n  max_requests: 22\nprobes:\n  enabled: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PANOPTES_BUDGET__MAX_REQUESTS", "33")
    settings = load_settings(path)
    assert settings.budget.max_requests == 33
    assert settings.probes.enabled is True


def test_missing_and_invalid_yaml_raise_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_settings(tmp_path / "missing.yaml")
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("budget:\n  max_requests: 0\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_settings(invalid)


def test_errors_share_base_class() -> None:
    assert all(
        issubclass(cls, PanoptesError)
        for cls in (SourceError, ProbeError, ConfigError, BudgetExceeded)
    )
    assert str(BudgetExceeded("limit")) == "limit"


def test_logging_modes_context_and_invalid_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(mode="prod", level="INFO")
    bind_run_context(run_id="r1", target="example.test")
    structlog.get_logger("panoptes.test").info("unit_event")
    captured = capsys.readouterr()
    assert "unit_event" in captured.err
    assert "run_id" in captured.err
    clear_run_context()
    configure_logging(mode="dev", level="DEBUG")
    with pytest.raises(ValueError):
        configure_logging(mode="unknown")
    with pytest.raises(ValueError):
        configure_logging(level="NO_SUCH_LEVEL")
    assert logging.getLogger().level == logging.DEBUG


@pytest.mark.asyncio
async def test_event_bus_fanout_and_cleanup() -> None:
    bus = EventBus(queue_size=2)
    first = await bus.subscribe()
    second = await bus.subscribe()
    event = RunStarted(run_id="r1", target="example.test")
    await bus.publish(event)
    assert await first.get() == event
    assert await second.get() == event
    assert bus.subscriber_count == 2
    await bus.unsubscribe(first)
    assert first._closed
    await bus.close()
    assert bus.subscriber_count == 0
    assert second._closed


@pytest.mark.asyncio
async def test_event_bus_backpressure_and_invalid_size() -> None:
    with pytest.raises(ValueError):
        EventBus(queue_size=0)
    bus = EventBus(queue_size=1)
    subscriber = await bus.subscribe()
    await bus.publish(AssetDiscovered(run_id="r", asset_id="a"))
    blocked = asyncio.create_task(bus.publish(AssetDiscovered(run_id="r", asset_id="b")))
    await asyncio.sleep(0)
    assert not blocked.done()
    assert (await subscriber.get()).asset_id == "a"
    await asyncio.wait_for(blocked, timeout=1)
    assert (await subscriber.get()).asset_id == "b"
    await bus.unsubscribe(subscriber)
    await bus.publish(AssetDiscovered(run_id="r", asset_id="c"))
