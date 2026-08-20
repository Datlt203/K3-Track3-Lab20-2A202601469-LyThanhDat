# Benchmark Report

| Run | Latency (s) | Cost (USD) | Quality | Citation cov. | Failure rate | Notes |
|---|---:|---:|---:|---:|---:|---|
| baseline | 4.14 | 0.0000 | 2.0 | 0% | 0% | routes= |
| multi-agent | 1.47 | 0.0000 | 10.0 | 100% | 0% | routes=researcher,analyst,writer |
| baseline | 1.33 | 0.0006 | 4.0 | 0% | 0% | routes= |
| multi-agent | 0.11 | 0.0000 | 10.0 | 100% | 0% | routes=researcher,analyst,writer |
| baseline | 0.89 | 0.0000 | 2.0 | 0% | 0% | routes= |
| multi-agent | 0.07 | 0.0000 | 10.0 | 100% | 0% | routes=researcher,analyst,writer |

## Analysis

- **baseline**: average latency 2.12s, quality 2.7/10, failure rate 0%.
- **multi-agent**: average latency 0.55s, quality 10.0/10, failure rate 0%.

### Failure modes

The main observed failure modes are missing evidence, provider/API errors, and citation loss during synthesis. The benchmark records these as a failed run when the state contains errors or no final answer. The multi-agent workflow reduces debugging ambiguity through route history and per-agent trace events, but it can still cost more latency and amplify an empty-search failure into a low-quality answer.
