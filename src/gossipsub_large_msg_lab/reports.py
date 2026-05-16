"""Report rendering helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .simulator import SimulationResult


def to_primitive(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_primitive(inner) for key, inner in asdict(value).items()}
    if isinstance(value, list):
        return [to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {key: to_primitive(item) for key, item in value.items()}
    return value


def result_to_json(result: SimulationResult) -> str:
    return json.dumps(to_primitive(result), indent=2, sort_keys=True)


def result_to_markdown(result: SimulationResult) -> str:
    avg = (
        f"{result.average_completion_latency_ms:.2f} ms"
        if result.average_completion_latency_ms is not None
        else "n/a"
    )
    max_latency = f"{result.max_completion_latency_ms} ms" if result.max_completion_latency_ms is not None else "n/a"
    lines = [
        "# Gossipsub Large Message Simulation Report",
        "",
        "This is a model-based simulation report, not a live libp2p network trace.",
        "",
        "## Scenario",
        "",
        f"- Peers: {result.config.peer_count}",
        f"- Mesh degree: {result.config.mesh_degree}",
        f"- Segment size: {result.config.segment_size} bytes",
        f"- Payload size: {result.config.payload_size} bytes",
        f"- Segments: {result.segment_count}",
        f"- Loss rate: {result.config.loss_rate}",
        f"- Duplicate rate: {result.config.duplicate_rate}",
        f"- Churn rate: {result.config.churn_rate}",
        "",
        "## Metrics",
        "",
        f"- Completed peers: {result.completed_peers}",
        f"- Completion rate: {result.completion_rate:.2%}",
        f"- Delivered events: {result.delivered_events}",
        f"- Dropped events: {result.dropped_events}",
        f"- Duplicate events: {result.duplicate_events}",
        f"- Average completion latency: {avg}",
        f"- Max completion latency: {max_latency}",
        f"- Max buffered bytes: {result.max_buffered_bytes}",
        f"- Churned peers: {', '.join(result.churned_peers) if result.churned_peers else 'none'}",
        "",
        "## Peer Results",
        "",
        "| Peer | Complete | Received | Missing | Duplicates | Rejected | Completed at |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for peer in result.peer_results:
        completed_at = str(peer.completed_at_ms) if peer.completed_at_ms is not None else "n/a"
        lines.append(
            f"| {peer.peer_id} | {peer.complete} | {peer.received_segments} | "
            f"{peer.missing_segments} | {peer.duplicates} | {peer.rejected} | {completed_at} |"
        )
    return "\n".join(lines) + "\n"


def write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
