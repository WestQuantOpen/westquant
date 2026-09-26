# WestQuant Open — Project Plan

> Open research infrastructure for AI x Quantum Algorithm Engineering

## Positioning

WestQuant Open is an open research infrastructure for generating machine-learning data from quantum programs, comparing quantum software stacks, and searching for better circuit representations and compilation strategies across frameworks and hardware targets.

The unique layer:

```
Quantum program -> representation -> transformation sequence -> hardware mapping -> result
```

## Terminology

Use **Representation-Transformation Scheduling (RTS)** or **Representation and Compilation Policy Search** instead of "scheduling" (which Qiskit uses for wall-clock timing).

Formalization:

```
pi = (r_0, T_1, r_1, T_2, ..., T_k, r_k)

where:
  r_i = representation
  T_i = transformation
  pi = compilation/representation policy

Optimize:
  pi* = argmin J(C, pi, H)

for circuit C, hardware target H, and objective:
  J = alpha*D + beta*G_2q + gamma*E + delta*T_c

where:
  D    = depth
  G_2q = two-qubit gates
  E    = estimated execution error
  T_c  = compilation time
```

## Two-step story

| Release | What | When |
|---------|------|------|
| **Paper/Release A** | WestQuantOpen infrastructure, tools, experiment platform | Now |
| **Paper/Release B** | WQT20 model that learns from and works on top of the infrastructure | Later |

This is research-clean: Paper A does not depend on the model working.

## Technical paper (working title)

**WestQuantOpen: Cross-Framework Quantum Program Optimization, Representation Scheduling, and ML Dataset Generation**

### Four main contributions

| Contribution | Content |
|-------------|---------|
| Cross-framework abstraction | Qiskit, PennyLane, Cirq, later Braket/Q# |
| Transformation provenance | Every step in an algorithm's change is recorded |
| ML dataset generation | Before/after pairs, actions, metrics, hardware targets |
| Representation-policy search | Systematic search for better transformation sequences |

WQT20 is mentioned only as a downstream use case.

## Central data format

Every WestQuant run produces:

```
x = (C, R, H, M)  ->  action a = T_i  ->  x' = (C', R', H, M')

reward: r = M(x) - M(x')
```

Example record:

```json
{
  "algorithm": "QFT",
  "qubits": 12,
  "framework": "Qiskit",
  "representation_before": "DAG",
  "action": "commute_controlled",
  "representation_after": "DAG",
  "depth_before": 184,
  "depth_after": 161,
  "two_qubit_before": 72,
  "two_qubit_after": 64,
  "target": "heavy_hex",
  "semantic_equivalence": "PASS"
}
```

This gives (s, a, s', r) tuples — ready for WQT training.

## Benchmark corpus

10 algorithm families, 20-50 instances each:

| Family | Sizes |
|--------|-------|
| GHZ | 4-100 qubits |
| QFT | 3-30 |
| Grover | 3-20 |
| Bernstein-Vazirani | 4-50 |
| Quantum Phase Estimation | 3-20 |
| QAOA MaxCut | multiple graph families |
| VQE ansatze | multiple molecule/ansatz types |
| Hamiltonian/Trotter simulation | varying steps |
| Quantum arithmetic | adders/multipliers |
| Random Clifford/general circuits | varying density |

Target: 1,000-10,000 benchmark circuits.

## 20 experiments

| # | Experiment | What WQO demonstrates | Primary metric |
|---|-----------|----------------------|----------------|
| 1 | Algorithm -> ML dataset | Generate training samples automatically | samples/s |
| 2 | Equivalent circuit augmentation | Create many semantically equivalent representations | unique valid circuits |
| 3 | Transformation trace dataset | Save every intermediate circuit | samples/algorithm |
| 4 | Cross-framework dataset | Same algorithm from Qiskit/PennyLane/Cirq -> common schema | representation agreement |
| 5 | Hardware-conditioned dataset | Same circuit compiled for different topologies/gatesets | dataset diversity |
| 6 | Fixed vs searched transformation order | Compare standard pipeline with WestQuant search | depth / 2Q gates |
| 7 | Representation scheduling | Let WQO search order between representations/transforms | objective improvement |
| 8 | Algorithm-specific schedules | QFT, Grover, QAOA get different optimal policies | improvement/family |
| 9 | Schedule transfer | Policy searched on 6-10 qubits tested on 20-50 | scaling/generalization |
| 10 | Pareto optimization | Depth vs 2Q gates vs compile time | Pareto frontier |
| 11 | Qiskit vs PennyLane vs Cirq | Same circuits and targets through each stack | depth/gates/runtime |
| 12 | Framework capability map | Map which transformations each framework offers | coverage |
| 13 | Cross-framework semantic preservation | Convert and verify algorithms between frameworks | equivalence rate |
| 14 | Round-trip conversion | Qiskit -> Cirq -> PennyLane -> back | semantic drift |
| 15 | Compilation determinism | Run same pipeline N times | variance |
| 16 | Regression detector | Benchmark two framework versions | changed outputs |
| 17 | Invalid transformation detection | Try transformation chains that break semantics | detection precision |
| 18 | Noise/hardware-aware optimization | Optimize against noise model instead of just gate count | expected fidelity |
| 19 | Search efficiency | Random search vs heuristics vs WestQuant search | quality/search cost |
| 20 | OOD algorithm test | Optimize circuits the search has never seen | OOD improvement |

### Priority experiments (do first)

1. **#1** ML dataset generation (hero demo: 1 algorithm -> thousands of ML examples)
2. **#6** Transformation-order search (fixed vs searched pipelines)
3. **#8** Algorithm-specific policies
4. **#11** Qiskit/PennyLane/Cirq benchmark shootout
5. **#18** Hardware/noise-aware optimization

## 6-week delivery plan

| Week | Delivery |
|------|----------|
| 1 | GitHub landing page + docs + architecture diagram |
| 2 | WestQuant Plugins public research release |
| 3 | Tests 1-5: automated ML data generation |
| 4 | Tests 6-10: representation/transformation scheduling |
| 5 | Tests 11-15: Qiskit vs PennyLane vs Cirq benchmark |
| 6 | Technical paper v0.1 + arXiv/Zenodo + public launch |

## Standardized output format

Every benchmark run produces:

| File | Content |
|------|---------|
| `results.json` | Structured metrics (depth, gates, time, equivalence) |
| `trace.jsonl` | One line per transformation step (provenance) |
| `dataset.parquet` | ML training data (s, a, s', r) tuples |
| `summary.md` | Human-readable summary with tables |
| `figure.png` | Visualization (Pareto front, bar chart, etc.) |

## Experiment metrics

Standardized as relative deltas for paired experiments:

```
Delta_D   = (D_WQ - D_baseline) / D_baseline
Delta_G2q = (G2q_WQ - G2q_base) / G2q_base
```

Plus: compilation time, semantic-equivalence pass rate, target validity, dataset throughput, number of unique states, number of unique transitions.

Report median/mean + bootstrap confidence intervals.

## Plugins release checklist

### A. Plugin packages
- [ ] westquant-qiskit (Qiskit transpiler plugins)
- [ ] westquant-pytket (pytket pass search)
- [ ] westquant-pennylane (PennyLane transform search)
- [ ] westquant-pulser (Pulser neutral-atom search)

### B. Examples
- [ ] `examples/01_qft_optimization.ipynb`
- [ ] `examples/02_generate_ml_dataset.ipynb`
- [ ] `examples/03_qiskit_vs_pennylane.ipynb`
- [ ] `examples/04_representation_search.ipynb`
- [ ] `examples/05_hardware_targeting.ipynb`

### C. Benchmarks
- [ ] `benchmarks/circuits/` (10 algorithm families)
- [ ] `benchmarks/protocols/` (experiment definitions)
- [ ] `benchmarks/results/` (output data)

### D. Reproducibility
- [ ] Version matrix (framework versions)
- [ ] Seeds and environment config
- [ ] Raw results archive
- [ ] Reproducible script

## Qiskit ecosystem

Submit to Qiskit Ecosystem: https://quantum.cloud.ibm.com/docs/en/guides/transpiler-plugins

Qiskit has official external transpiler plugin support and an ecosystem program. This is the primary distribution channel.

## Weekly reminder

A macOS launchd agent sends a notification every Monday at 9:00 AM with the current week's tasks. The reminder cycles through the 6-week plan.

To test the reminder:
```bash
bash ~/.local/bin/wqo-weekly-reminder.sh
```

To reset the week counter:
```bash
echo "1" > ~/.config/devin/wqo_week.txt
```
