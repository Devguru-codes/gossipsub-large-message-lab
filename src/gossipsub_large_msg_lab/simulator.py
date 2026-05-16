"""Deterministic gossip-style propagation simulator."""

from __future__ import annotations

import heapq
import random
from collections import defaultdict
from dataclasses import dataclass, field

from .protocol import LargeMessage, Segment, Segmenter
from .reassembly import ReassemblyBuffer


@dataclass(frozen=True)
class SimulationConfig:
    peer_count: int = 12
    mesh_degree: int = 4
    segment_size: int = 1024
    payload_size: int = 8192
    fanout: int = 3
    loss_rate: float = 0.0
    duplicate_rate: float = 0.0
    churn_rate: float = 0.0
    min_latency_ms: int = 5
    max_latency_ms: int = 50
    max_rounds: int = 500
    max_message_size: int = 16 * 1024 * 1024
    seed: int = 1
    topic: str = "large-messages"
    publisher: str = "peer-0"

    @classmethod
    def from_dict(cls, data: dict) -> SimulationConfig:
        valid = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        unknown = sorted(set(data) - valid)
        if unknown:
            raise ValueError(f"unknown config keys: {', '.join(unknown)}")
        config = cls(**data)
        config.validate()
        return config

    def validate(self) -> None:
        if self.peer_count < 2:
            raise ValueError("peer_count must be at least 2")
        if self.mesh_degree < 1 or self.mesh_degree >= self.peer_count:
            raise ValueError("mesh_degree must be between 1 and peer_count - 1")
        if self.segment_size <= 0:
            raise ValueError("segment_size must be positive")
        if self.payload_size < 0:
            raise ValueError("payload_size must be non-negative")
        if self.fanout < 1:
            raise ValueError("fanout must be positive")
        for name, value in {
            "loss_rate": self.loss_rate,
            "duplicate_rate": self.duplicate_rate,
            "churn_rate": self.churn_rate,
        }.items():
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.min_latency_ms < 0 or self.max_latency_ms < self.min_latency_ms:
            raise ValueError("latency bounds are invalid")
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be positive")
        if self.payload_size > self.max_message_size:
            raise ValueError("payload_size exceeds max_message_size")


@dataclass(frozen=True)
class PeerResult:
    peer_id: str
    received_segments: int
    missing_segments: int
    duplicates: int
    rejected: int
    complete: bool
    completed_at_ms: int | None
    buffered_bytes: int


@dataclass(frozen=True)
class SimulationResult:
    config: SimulationConfig
    message_id: str
    segment_count: int
    total_events: int
    delivered_events: int
    dropped_events: int
    duplicate_events: int
    churned_peers: list[str]
    completed_peers: int
    completion_rate: float
    max_completion_latency_ms: int | None
    average_completion_latency_ms: float | None
    max_buffered_bytes: int
    peer_results: list[PeerResult] = field(default_factory=list)


@dataclass(order=True)
class _Event:
    at_ms: int
    order: int
    sender: str
    receiver: str
    segment: Segment


class Simulator:
    """Run deterministic large-message propagation experiments."""

    def __init__(self, config: SimulationConfig) -> None:
        config.validate()
        self.config = config
        self.random = random.Random(config.seed)

    def run(self) -> SimulationResult:
        payload = self._payload(self.config.payload_size)
        message = LargeMessage(topic=self.config.topic, payload=payload, publisher=self.config.publisher)
        segments = Segmenter(self.config.segment_size).segment(message)
        peers = [f"peer-{index}" for index in range(self.config.peer_count)]
        publisher = self.config.publisher if self.config.publisher in peers else peers[0]
        active = self._active_peers(peers, publisher)
        mesh = self._build_mesh(peers)
        buffers = {
            peer: ReassemblyBuffer(
                message_id=message.message_id,
                max_segment_size=self.config.segment_size,
                max_message_size=self.config.max_message_size,
            )
            for peer in peers
        }
        completed_at: dict[str, int] = {}
        seen_by_peer: dict[str, set[str]] = defaultdict(set)
        queue: list[_Event] = []
        order = 0
        delivered_events = 0
        dropped_events = 0
        duplicate_events = 0

        for segment in segments:
            for receiver in self._choose_neighbors(mesh[publisher], active, self.config.fanout):
                order = self._schedule(queue, order, 0, publisher, receiver, segment)

        while queue and delivered_events < self.config.max_rounds:
            event = heapq.heappop(queue)
            if event.receiver not in active:
                dropped_events += 1
                continue
            if self.random.random() < self.config.loss_rate:
                dropped_events += 1
                continue

            delivered_events += 1
            status = buffers[event.receiver].accept(event.segment)
            already_seen = event.segment.segment_id in seen_by_peer[event.receiver]
            seen_by_peer[event.receiver].add(event.segment.segment_id)
            if status.duplicate or already_seen:
                duplicate_events += 1
            if status.complete and event.receiver not in completed_at:
                completed_at[event.receiver] = event.at_ms

            if status.accepted and not status.duplicate and not already_seen:
                for neighbor in self._choose_neighbors(
                    [peer for peer in mesh[event.receiver] if peer != event.sender],
                    active,
                    self.config.fanout,
                ):
                    order = self._schedule(queue, order, event.at_ms, event.receiver, neighbor, event.segment)
                    if self.random.random() < self.config.duplicate_rate:
                        order = self._schedule(queue, order, event.at_ms, event.receiver, neighbor, event.segment)

        peer_results = []
        for peer in peers:
            buffer = buffers[peer]
            completed = peer in completed_at
            peer_results.append(
                PeerResult(
                    peer_id=peer,
                    received_segments=len(buffer.segments),
                    missing_segments=len(buffer.missing_indices),
                    duplicates=buffer.duplicate_count,
                    rejected=buffer.rejected_count,
                    complete=completed,
                    completed_at_ms=completed_at.get(peer),
                    buffered_bytes=buffer.buffered_bytes,
                )
            )

        receiver_count = len([peer for peer in peers if peer != publisher and peer in active])
        completed_peers = len([peer for peer in completed_at if peer != publisher])
        latencies = [value for peer, value in completed_at.items() if peer != publisher]
        return SimulationResult(
            config=self.config,
            message_id=message.message_id,
            segment_count=len(segments),
            total_events=delivered_events + dropped_events,
            delivered_events=delivered_events,
            dropped_events=dropped_events,
            duplicate_events=duplicate_events,
            churned_peers=sorted(set(peers) - active),
            completed_peers=completed_peers,
            completion_rate=completed_peers / receiver_count if receiver_count else 0.0,
            max_completion_latency_ms=max(latencies) if latencies else None,
            average_completion_latency_ms=sum(latencies) / len(latencies) if latencies else None,
            max_buffered_bytes=max((result.buffered_bytes for result in peer_results), default=0),
            peer_results=peer_results,
        )

    def _active_peers(self, peers: list[str], publisher: str) -> set[str]:
        active = set()
        for peer in peers:
            if peer == publisher or self.random.random() >= self.config.churn_rate:
                active.add(peer)
        return active

    def _build_mesh(self, peers: list[str]) -> dict[str, list[str]]:
        mesh: dict[str, set[str]] = {peer: set() for peer in peers}
        degree = self.config.mesh_degree
        for index, peer in enumerate(peers):
            for offset in range(1, degree + 1):
                other = peers[(index + offset) % len(peers)]
                mesh[peer].add(other)
                mesh[other].add(peer)
        return {peer: sorted(neighbors) for peer, neighbors in mesh.items()}

    def _choose_neighbors(self, candidates: list[str], active: set[str], limit: int) -> list[str]:
        choices = [peer for peer in candidates if peer in active]
        self.random.shuffle(choices)
        return choices[:limit]

    def _schedule(
        self,
        queue: list[_Event],
        order: int,
        now_ms: int,
        sender: str,
        receiver: str,
        segment: Segment,
    ) -> int:
        latency = self.random.randint(self.config.min_latency_ms, self.config.max_latency_ms)
        heapq.heappush(queue, _Event(now_ms + latency, order, sender, receiver, segment))
        return order + 1

    def _payload(self, size: int) -> bytes:
        alphabet = b"gossipsub-large-message-lab:"
        if size == 0:
            return b""
        out = bytearray()
        while len(out) < size:
            out.extend(alphabet)
        return bytes(out[:size])
