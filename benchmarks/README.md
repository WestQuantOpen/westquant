# WestQuant Open — Benchmarks

Standardized benchmark circuits, experiment protocols, and results.

## Structure

```
benchmarks/
├── circuits/          # 10 algorithm families, 20-50 instances each
│   ├── ghz/
│   ├── qft/
│   ├── grover/
│   ├── bernstein_vazirani/
│   ├── qpe/
│   ├── qaoa_maxcut/
│   ├── vqe_ansatze/
│   ├── trotter_simulation/
│   ├── quantum_arithmetic/
│   └── random_clifford/
├── protocols/         # Experiment definitions (20 experiments)
│   ├── 01_ml_dataset_generation.yaml
│   ├── 06_fixed_vs_searched.yaml
│   ├── 11_framework_shootout.yaml
│   └── 18_noise_aware.yaml
└── results/          # Output data (results.json, trace.jsonl, dataset.parquet, summary.md, figure.png)
```

## Algorithm families

| Family | Sizes | Instances |
|--------|-------|-----------|
| GHZ | 4-100 qubits | 20 |
| QFT | 3-30 | 30 |
| Grover | 3-20 | 20 |
| Bernstein-Vazirani | 4-50 | 20 |
| Quantum Phase Estimation | 3-20 | 20 |
| QAOA MaxCut | multiple graph families | 50 |
| VQE ansatze | multiple molecule/ansatz types | 30 |
| Hamiltonian/Trotter simulation | varying steps | 20 |
| Quantum arithmetic | adders/multipliers | 20 |
| Random Clifford/general circuits | varying density | 50 |

Target: ~2,000 benchmark circuits.

## Standardized output

Every benchmark run produces:

| File | Content |
|------|---------|
| `results.json` | Structured metrics (depth, gates, time, equivalence) |
| `trace.jsonl` | One line per transformation step (provenance) |
| `dataset.parquet` | ML training data (s, a, s', r) tuples |
| `summary.md` | Human-readable summary with tables |
| `figure.png` | Visualization |

## Metrics

Reported as relative deltas for paired experiments:

```
Delta_D   = (D_WQ - D_baseline) / D_baseline
Delta_G2q = (G2q_WQ - G2q_base) / G2q_base
```

Plus: compilation time, semantic-equivalence pass rate, target validity, dataset throughput, unique states, unique transitions.

Reported as: median/mean + bootstrap confidence intervals.
