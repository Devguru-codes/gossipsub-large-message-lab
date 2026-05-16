import pytest

from gossipsub_large_msg_lab.protocol import LargeMessage, Segmenter
from gossipsub_large_msg_lab.reassembly import ReassemblyBuffer


def test_reassembly_accepts_out_of_order_segments() -> None:
    message = LargeMessage(topic="t", publisher="p", payload=b"abcdefghij")
    segments = Segmenter(4).segment(message)
    buffer = ReassemblyBuffer(message.message_id, max_segment_size=4, max_message_size=100)

    buffer.accept(segments[2])
    buffer.accept(segments[0])
    status = buffer.accept(segments[1])

    assert status.complete
    assert buffer.reconstruct() == message.payload


def test_reassembly_tracks_duplicates_and_missing_segments() -> None:
    message = LargeMessage(topic="t", publisher="p", payload=b"abcdefghij")
    segments = Segmenter(4).segment(message)
    buffer = ReassemblyBuffer(message.message_id, max_segment_size=4, max_message_size=100)

    buffer.accept(segments[0])
    duplicate = buffer.accept(segments[0])

    assert duplicate.duplicate
    assert buffer.duplicate_count == 1
    assert buffer.missing_indices == [1, 2]
    with pytest.raises(ValueError):
        buffer.reconstruct()


def test_reassembly_rejects_message_size_over_limit() -> None:
    message = LargeMessage(topic="t", publisher="p", payload=b"abcdefghij")
    segment = Segmenter(4).segment(message)[0]
    buffer = ReassemblyBuffer(message.message_id, max_segment_size=4, max_message_size=5)

    status = buffer.accept(segment)

    assert not status.accepted
    assert buffer.rejected_count == 1
