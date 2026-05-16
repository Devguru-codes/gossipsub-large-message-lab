"""Receiver-side reassembly state for segmented messages."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .protocol import Segment, ValidationCode, ValidationResult


@dataclass
class ReassemblyStatus:
    accepted: bool
    duplicate: bool
    complete: bool
    validation: ValidationResult


@dataclass
class ReassemblyBuffer:
    """Collect validated segments for one message until complete."""

    message_id: str
    max_segment_size: int
    max_message_size: int
    total: int | None = None
    message_hash: str | None = None
    message_size: int | None = None
    segments: dict[int, bytes] = field(default_factory=dict)
    duplicate_count: int = 0
    rejected_count: int = 0

    def accept(self, segment: Segment) -> ReassemblyStatus:
        validation = self._validate_against_buffer(segment)
        if not validation.ok:
            self.rejected_count += 1
            return ReassemblyStatus(False, False, False, validation)

        if segment.index in self.segments:
            self.duplicate_count += 1
            return ReassemblyStatus(True, True, self.is_complete, validation)

        if self.total is None:
            self.total = segment.total
            self.message_hash = segment.message_hash
            self.message_size = segment.message_size

        self.segments[segment.index] = segment.payload
        return ReassemblyStatus(True, False, self.is_complete, validation)

    @property
    def is_complete(self) -> bool:
        return self.total is not None and len(self.segments) == self.total

    @property
    def missing_indices(self) -> list[int]:
        if self.total is None:
            return []
        return [index for index in range(self.total) if index not in self.segments]

    @property
    def buffered_bytes(self) -> int:
        return sum(len(payload) for payload in self.segments.values())

    def reconstruct(self) -> bytes:
        if not self.is_complete:
            missing = ", ".join(str(index) for index in self.missing_indices)
            raise ValueError(f"message is incomplete; missing segments: {missing}")
        payload = b"".join(self.segments[index] for index in range(self.total or 0))
        if len(payload) != self.message_size:
            raise ValueError("reconstructed payload size does not match metadata")
        if hashlib.sha256(payload).hexdigest() != self.message_hash:
            raise ValueError("reconstructed payload hash does not match metadata")
        return payload

    def _validate_against_buffer(self, segment: Segment) -> ValidationResult:
        base = segment.validate(self.max_segment_size)
        if not base.ok:
            return base
        if segment.message_id != self.message_id:
            return ValidationResult(ValidationCode.MESSAGE_MISMATCH, "segment belongs to a different message")
        if segment.message_size > self.max_message_size:
            return ValidationResult(ValidationCode.INVALID_SIZE, "message size exceeds configured bound")
        if self.total is not None and segment.total != self.total:
            return ValidationResult(ValidationCode.INVALID_TOTAL, "segment total changed during reassembly")
        if self.message_hash is not None and segment.message_hash != self.message_hash:
            return ValidationResult(ValidationCode.INVALID_HASH, "message hash changed during reassembly")
        if self.message_size is not None and segment.message_size != self.message_size:
            return ValidationResult(ValidationCode.INVALID_SIZE, "message size changed during reassembly")
        return base
