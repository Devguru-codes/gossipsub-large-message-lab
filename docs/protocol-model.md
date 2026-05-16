# Protocol Model

This toolkit models a possible Gossipsub 1.4 large-message layer for research
and specification work. It does not define a final libp2p wire format.

## Objects

- `LargeMessage`: the application payload before segmentation.
- `Segment`: a bounded byte range plus metadata for validation and reassembly.
- `ReassemblyBuffer`: receiver-side state for one message ID.

## Segment metadata

Each simulated segment carries:

- message ID
- topic
- publisher
- segment index
- total segment count
- segment payload
- original message size
- original message hash
- segment hash

The message ID is derived deterministically from topic, publisher, and payload.
That is useful for repeatable research, but a production specification may bind
IDs differently.

## Delivery rule

A receiver delivers a reconstructed message only after:

- every segment index from `0` to `total - 1` is present
- each segment hash is valid
- metadata remains consistent across all segments
- the reconstructed payload size matches the advertised size
- the reconstructed payload hash matches the advertised message hash
