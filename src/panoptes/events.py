"""Typed asynchronous pub/sub event bus with bounded subscriber queues."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class PanoptesEvent:
    """Base event emitted during a PANOPTES run."""

    run_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class RunStarted(PanoptesEvent):
    """A run has started."""

    target: str = ""


@dataclass(frozen=True, slots=True)
class AssetDiscovered(PanoptesEvent):
    """An asset was discovered."""

    asset_id: str = ""
    asset_type: str = "unknown"


@dataclass(frozen=True, slots=True)
class EdgeDiscovered(PanoptesEvent):
    """A graph edge was discovered."""

    edge_id: str = ""
    source_id: str = ""
    target_id: str = ""


@dataclass(frozen=True, slots=True)
class FindingCreated(PanoptesEvent):
    """A finding was created."""

    finding_id: str = ""
    severity: str = "info"


@dataclass(frozen=True, slots=True)
class RunFinished(PanoptesEvent):
    """A run has finished."""

    success: bool = True


class Subscription[EventT: PanoptesEvent]:
    """Consumer subscription backed by a bounded asyncio queue."""

    def __init__(self, queue: asyncio.Queue[EventT], *, maxsize: int) -> None:
        self._queue = queue
        self.maxsize = maxsize
        self._closed = False

    async def get(self) -> EventT:
        """Wait for the next event."""
        if self._closed and self._queue.empty():
            raise StopAsyncIteration
        return await self._queue.get()

    async def __aiter__(self) -> AsyncIterator[EventT]:
        while not self._closed:
            try:
                yield await self.get()
            except StopAsyncIteration:
                return

    def close(self) -> None:
        """Close the subscription and discard pending events."""
        self._closed = True
        while not self._queue.empty():
            self._queue.get_nowait()


class EventBus:
    """Fan out events to bounded queues; publish waits rather than dropping."""

    def __init__(self, *, queue_size: int = 100) -> None:
        if queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        self.queue_size = queue_size
        self._subscribers: set[Subscription[PanoptesEvent]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> Subscription[PanoptesEvent]:
        """Register a subscriber."""
        subscription: Subscription[PanoptesEvent] = Subscription(
            asyncio.Queue(maxsize=self.queue_size), maxsize=self.queue_size
        )
        async with self._lock:
            self._subscribers.add(subscription)
        return subscription

    async def unsubscribe(self, subscription: Subscription[PanoptesEvent]) -> None:
        """Remove and close a subscriber."""
        async with self._lock:
            self._subscribers.discard(subscription)
            subscription.close()

    async def publish(self, event: PanoptesEvent) -> None:
        """Deliver to all current subscribers with bounded-memory backpressure."""
        async with self._lock:
            subscribers = tuple(self._subscribers)
        for subscription in subscribers:
            if not subscription._closed:
                await subscription._queue.put(event)

    async def close(self) -> None:
        """Close all subscriptions and clear queued events."""
        async with self._lock:
            subscribers = tuple(self._subscribers)
            self._subscribers.clear()
        for subscription in subscribers:
            subscription.close()

    @property
    def subscriber_count(self) -> int:
        """Number of registered subscribers."""
        return len(self._subscribers)
