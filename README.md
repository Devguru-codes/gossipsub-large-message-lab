# Gossipsub Large Message Research Toolkit

This repository is a standalone research toolkit for exploring large-message
handling designs for Gossipsub 1.4. It models segmentation, propagation,
reassembly, resource limits, and security considerations in a reproducible
Python package.

It is not a production libp2p implementation. The simulator deliberately labels
its behavior as model-based so results can support specification work without
overstating compatibility with real `py-libp2p`, `nim-libp2p`, or `go-libp2p`
nodes.

## Why this exists

The C4GT 2026 issue for Gossipsub 1.4 large-message handling asks for a
specification PR, wire-format documentation, segmentation and reconstruction
mechanisms, interoperability validation planning, security considerations, and a
path toward Working Draft / Candidate Recommendation status.

This toolkit helps prepare that work by making the protocol questions concrete:

- how a large payload is split into bounded segments
- how segment metadata can be validated
- how peers collect out-of-order and duplicate segments
- how loss, latency, churn, and fanout affect completion
- which security threats need normative spec language

## Quick start

```powershell
python -m pip install -e .
python -m pytest
python -m gossipsub_large_msg_lab segment --text "hello large pubsub" --segment-size 5
python -m gossipsub_large_msg_lab simulate examples/basic-scenario.json --markdown
python -m gossipsub_large_msg_lab security-matrix
```

## Project layout

```text
src/gossipsub_large_msg_lab/
  protocol.py      typed message, segment, and validation model
  reassembly.py    receiver-side segment collection and integrity checks
  simulator.py     deterministic gossip-style propagation simulator
  reports.py       JSON and Markdown report rendering
  security.py      documented threat and mitigation matrix
  cli.py           Typer CLI
docs/
  protocol-model.md
  simulator-assumptions.md
  security-analysis.md
  interoperability-plan.md
  candidate-recommendation.md
examples/
  basic-scenario.json
tests/
```

## Research boundaries

The toolkit models behavior that a Gossipsub 1.4 specification may choose to
standardize. It does not define final wire compatibility and does not speak the
libp2p protocol on the network. Future work can connect the scenario format to
real `py-libp2p` and `nim-libp2p` harnesses.
