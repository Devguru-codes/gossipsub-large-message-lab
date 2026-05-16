# Gossipsub Large Message Simulation Report

This is a model-based simulation report, not a live libp2p network trace.

## Scenario

- Peers: 12
- Mesh degree: 3
- Segment size: 512 bytes
- Payload size: 4096 bytes
- Segments: 8
- Loss rate: 0.02
- Duplicate rate: 0.05
- Churn rate: 0.0

## Metrics

- Completed peers: 11
- Completion rate: 100.00%
- Delivered events: 325
- Dropped events: 7
- Duplicate events: 229
- Average completion latency: 65.82 ms
- Max completion latency: 89 ms
- Max buffered bytes: 4096
- Churned peers: none

## Peer Results

| Peer | Complete | Received | Missing | Duplicates | Rejected | Completed at |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| peer-0 | True | 8 | 0 | 7 | 0 | 96 |
| peer-1 | True | 8 | 0 | 24 | 0 | 63 |
| peer-2 | True | 8 | 0 | 25 | 0 | 58 |
| peer-3 | True | 8 | 0 | 21 | 0 | 56 |
| peer-4 | True | 8 | 0 | 22 | 0 | 68 |
| peer-5 | True | 8 | 0 | 22 | 0 | 57 |
| peer-6 | True | 8 | 0 | 18 | 0 | 89 |
| peer-7 | True | 8 | 0 | 20 | 0 | 77 |
| peer-8 | True | 8 | 0 | 16 | 0 | 78 |
| peer-9 | True | 8 | 0 | 22 | 0 | 76 |
| peer-10 | True | 8 | 0 | 12 | 0 | 61 |
| peer-11 | True | 8 | 0 | 20 | 0 | 41 |
