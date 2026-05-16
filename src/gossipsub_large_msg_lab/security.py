"""Security matrix for large-message handling discussions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Threat:
    name: str
    impact: str
    detection: str
    mitigation: str
    spec_requirement: str


THREATS: list[Threat] = [
    Threat(
        name="Reassembly state exhaustion",
        impact="A peer stores many incomplete messages until memory is exhausted.",
        detection="Track incomplete buffers, buffered bytes, and message age per peer/topic.",
        mitigation="Apply max message size, max incomplete messages, TTL, and peer scoring penalties.",
        spec_requirement="Implementations must bound reassembly state and expire incomplete messages.",
    ),
    Threat(
        name="Segment flooding",
        impact="Attackers send many valid-looking segments that consume bandwidth and validation work.",
        detection="Measure segment rate per peer and ratio of useful to rejected or duplicate segments.",
        mitigation="Rate-limit segment intake and penalize peers that exceed duplicate or invalid thresholds.",
        spec_requirement="Segment validation and resource accounting must happen before buffering.",
    ),
    Threat(
        name="Inconsistent metadata",
        impact="Peers receive conflicting totals, sizes, or message hashes for the same message ID.",
        detection="Compare every segment against established buffer metadata.",
        mitigation="Reject inconsistent segments and record the sender for scoring.",
        spec_requirement="A message ID must bind topic, publisher, payload commitment, and segment metadata policy.",
    ),
    Threat(
        name="Duplicate amplification",
        impact="Repeated segment forwarding increases mesh bandwidth without improving completion.",
        detection="Count duplicate segment IDs per peer and per topic.",
        mitigation="Use seen caches, bounded retransmission, and duplicate-aware forwarding.",
        spec_requirement="Implementations should suppress already-seen segments before forwarding.",
    ),
    Threat(
        name="Malformed integrity data",
        impact="Invalid hashes cause wasted reassembly work or corrupted delivery.",
        detection="Validate segment hash on receipt and reconstructed message hash before application delivery.",
        mitigation="Reject invalid segments and never deliver reconstructed messages before final integrity checks.",
        spec_requirement="Receivers must verify segment integrity and full-message integrity.",
    ),
    Threat(
        name="Slow incomplete message attack",
        impact="A peer sends only enough segments to keep buffers alive but never completes a message.",
        detection="Track last-update time and completion progress for each buffer.",
        mitigation="Expire stale buffers and require progress-based retention policies.",
        spec_requirement="The spec should define expiry guidance for incomplete large messages.",
    ),
]


def matrix_to_markdown(threats: list[Threat] | None = None) -> str:
    rows = threats or THREATS
    lines = [
        "# Large Message Handling Security Matrix",
        "",
        "| Threat | Impact | Detection | Mitigation | Spec Requirement |",
        "| --- | --- | --- | --- | --- |",
    ]
    for threat in rows:
        lines.append(
            f"| {threat.name} | {threat.impact} | {threat.detection} | "
            f"{threat.mitigation} | {threat.spec_requirement} |"
        )
    return "\n".join(lines) + "\n"
