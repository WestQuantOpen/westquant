# WestQuant Open — Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          WestQuant Open Layer            │
                    │                                         │
                    │   Quantum program                        │
                    │        │                                │
                    │        ▼                                │
                    │   ┌─────────┐    ┌──────────────┐       │
                    │   │  WQIR   │───▶│  RepGraph    │       │
                    │   │ (IR)    │    │  (search     │       │
                    │   └────┬────┘    │   space)     │       │
                    │        │         └──────┬───────┘       │
                    │        ▼                │              │
                    │   ┌─────────────┐        │              │
                    │   │ Transform   │◀───────┘              │
                    │   │ Registry    │                       │
                    │   │ (15+ ops)   │                       │
                    │   └─────┬───────┘                       │
                    │         │                               │
                    │         ▼                               │
                    │   ┌─────────────┐    ┌──────────────┐   │
                    │   │  Verifier   │───▶│  Planner     │   │
                    │   │ (EXACT/     │    │ (SAFE/       │   │
                    │   │  EQUIV/     │    │  BALANCED/   │   │
                    │   │  APPROX)    │    │  AGGRESSIVE) │   │
                    │   └─────────────┘    └──────────────┘   │
                    │         │                               │
                    │         ▼                               │
                    │   ┌─────────────────────────────┐        │
                    │   │  Output:                    │        │
                    │   │  • Optimized circuit        │        │
                    │   │  • ML dataset (s,a,s',r)   │        │
                    │   │  • Provenance trace         │        │
                    │   │  • Benchmark results       │        │
                    │   └─────────────────────────────┘        │
                    └─────────────────────────────────────────┘
                         ▲           ▲           ▲
                         │           │           │
                    ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
                    │ Qiskit  │ │ PennyLane│ │  Cirq   │
                    │ Plugin  │ │ Plugin  │ │ Bridge  │
                    └─────────┘ └─────────┘ └─────────┘
                         │           │           │
                         ▼           ▼           ▼
                    ┌─────────────────────────────────────┐
                    │        Hardware Targets               │
                    │  superconducting | trapped ion |       │
                    │  neutral atom | simulator | FT-ideal │
                    └─────────────────────────────────────┘
```

## Data flow

```
Input:  Quantum program (QASM, circuit object, algorithm spec)
           │
           ▼
WQIR:    Framework-neutral intermediate representation
           │
           ▼
Search:  RepGraph explores transformation sequences
         pi = (r_0, T_1, r_1, T_2, ..., T_k, r_k)
           │
           ▼
Verify:  Each step independently verified (EXACT / EQUIV / APPROX)
           │
           ▼
Plan:    Pareto-optimal plans (SAFE / BALANCED / AGGRESSIVE)
           │
           ▼
Output:  Optimized circuit + ML dataset + provenance trace
```

## ML dataset generation

Every transformation produces a training tuple:

```
state      = (circuit, representation, hardware, metrics)
action     = transformation T_i
next_state = (circuit', representation', hardware, metrics')
reward     = M(state) - M(next_state)

=> (s, a, s', r) for reinforcement learning
```

One algorithm (e.g., QFT) can produce thousands of labeled examples through:
- Multiple representations (DAG, graph, tensor)
- Multiple transformation sequences
- Multiple hardware targets
- Multiple objective functions
