from gossipsub_large_msg_lab.protocol import LargeMessage, Segmenter, ValidationCode


def test_segmenter_creates_bounded_segments() -> None:
    message = LargeMessage(topic="t", publisher="p", payload=b"abcdefghij")
    segments = Segmenter(4).segment(message)

    assert [len(segment.payload) for segment in segments] == [4, 4, 2]
    assert [segment.index for segment in segments] == [0, 1, 2]
    assert all(segment.total == 3 for segment in segments)
    assert all(segment.message_id == message.message_id for segment in segments)


def test_segment_validation_rejects_hash_mismatch() -> None:
    message = LargeMessage(topic="t", publisher="p", payload=b"abcdef")
    segment = Segmenter(3).segment(message)[0]
    broken = segment.__class__(
        **{
            **segment.__dict__,
            "payload": b"xxx",
        }
    )

    result = broken.validate(max_segment_size=3)

    assert result.code is ValidationCode.INVALID_HASH
