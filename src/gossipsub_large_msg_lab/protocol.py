"""Protocol-facing data model for simulated large-message handling.

The types in this module are intentionally small and explicit. They model the
metadata a specification needs to discuss without claiming to be a final libp2p
wire format.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class ValidationCode(str, Enum):
    VALID = "valid"
    INVALID_INDEX = "invalid_index"
    INVALID_TOTAL = "invalid_total"
    INVALID_SIZE = "invalid_size"
    INVALID_HASH = "invalid_hash"
    MESSAGE_MISMATCH = "message_mismatch"


@dataclass(frozen=True)
class ValidationResult:
    code: ValidationCode
    detail: str

    @property
    def ok(self) -> bool:
        return self.code is ValidationCode.VALID


@dataclass(frozen=True)
class LargeMessage:
    """Application payload before segmentation."""

    topic: str
    payload: bytes
    publisher: str = "publisher"

    @property
    def message_id(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.topic.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self.publisher.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self.payload)
        return digest.hexdigest()

    @property
    def payload_hash(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


@dataclass(frozen=True)
class Segment:
    """A bounded chunk plus metadata needed for simulated reassembly."""

    message_id: str
    topic: str
    publisher: str
    index: int
    total: int
    payload: bytes
    message_size: int
    message_hash: str
    segment_hash: str

    @property
    def segment_id(self) -> str:
        return f"{self.message_id}:{self.index}"

    @classmethod
    def create(
        cls,
        *,
        message: LargeMessage,
        index: int,
        total: int,
        payload: bytes,
    ) -> Segment:
        return cls(
            message_id=message.message_id,
            topic=message.topic,
            publisher=message.publisher,
            index=index,
            total=total,
            payload=payload,
            message_size=len(message.payload),
            message_hash=message.payload_hash,
            segment_hash=hashlib.sha256(payload).hexdigest(),
        )

    def validate(self, max_segment_size: int | None = None) -> ValidationResult:
        if self.total <= 0:
            return ValidationResult(ValidationCode.INVALID_TOTAL, "segment total must be positive")
        if self.index < 0 or self.index >= self.total:
            return ValidationResult(ValidationCode.INVALID_INDEX, "segment index is outside total")
        if max_segment_size is not None and len(self.payload) > max_segment_size:
            return ValidationResult(ValidationCode.INVALID_SIZE, "segment payload exceeds configured bound")
        if hashlib.sha256(self.payload).hexdigest() != self.segment_hash:
            return ValidationResult(ValidationCode.INVALID_HASH, "segment payload hash mismatch")
        return ValidationResult(ValidationCode.VALID, "segment is valid")


class Segmenter:
    """Split large messages into deterministic bounded segments."""

    def __init__(self, segment_size: int) -> None:
        if segment_size <= 0:
            raise ValueError("segment_size must be positive")
        self.segment_size = segment_size

    def segment(self, message: LargeMessage) -> list[Segment]:
        if not message.payload:
            chunks = [b""]
        else:
            chunks = list(_chunk_bytes(message.payload, self.segment_size))
        total = len(chunks)
        return [
            Segment.create(message=message, index=index, total=total, payload=payload)
            for index, payload in enumerate(chunks)
        ]


def _chunk_bytes(payload: bytes, size: int) -> Iterable[bytes]:
    for offset in range(0, len(payload), size):
        yield payload[offset : offset + size]
