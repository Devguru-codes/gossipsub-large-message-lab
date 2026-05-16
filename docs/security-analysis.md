# Security Analysis

Large-message support increases resource risk because peers may need to hold
partial state before a message can be delivered. The toolkit therefore treats
resource accounting as part of the protocol model.

Primary concerns:

- reassembly state exhaustion
- segment flooding
- inconsistent metadata
- duplicate amplification
- malformed integrity data
- slow incomplete-message attacks

The CLI command below emits the maintained threat matrix:

```powershell
python -m gossipsub_large_msg_lab security-matrix
```

Specification work should convert the strongest mitigations into normative
language, especially around bounded buffering, validation-before-buffering, final
message integrity verification, and expiry of incomplete state.
