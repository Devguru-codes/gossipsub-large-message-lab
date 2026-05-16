# Simulator Assumptions

The simulator is a deterministic model for comparing large-message propagation
strategies. It is intentionally smaller than a real Gossipsub network.

## Modeled behavior

- fixed peer count
- ring-like mesh construction with configurable degree
- bounded segment size
- eager forwarding to a limited fanout
- random latency per event
- configurable loss, duplicate delivery, and churn
- per-peer reassembly buffers
- duplicate suppression based on segment IDs

## Not modeled

- real libp2p peer negotiation
- RPC framing
- IHAVE/IWANT control message details
- peer scoring internals
- topic graft/prune behavior
- transport backpressure
- NAT traversal

Simulation results should be read as design evidence and regression-friendly
scenario output, not as performance claims about deployed libp2p networks.
