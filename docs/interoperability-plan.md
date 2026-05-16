# Interoperability Plan

Version 1 of this toolkit does not run real `py-libp2p` or `nim-libp2p`
implementations. It defines scenario concepts that can later be mapped to an
interop harness.

## Candidate scenarios

- one sender, one receiver, single large message
- multi-peer mesh with one large message
- out-of-order segment arrival
- missing segment recovery
- duplicate segment suppression
- malformed segment rejection
- concurrent large messages on one topic
- high latency and packet loss
- peer churn during propagation
- maximum configured message size

## Expected harness shape

A future harness should:

- start independent implementation nodes
- configure a shared topic and large-message capability
- send payloads with known hashes
- record segment-level and reconstructed-message observations
- compare sender payload hash with receiver payload hash
- export a report that can be referenced from the libp2p specification PR
