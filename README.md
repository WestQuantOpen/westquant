# WestQuant Open

**Search the representation, not just the parameters.**

WestQuant Open is an open-source representation-search layer for quantum computing. It searches alternative compilation and representation paths across multiple software stacks, while preserving verification and full provenance.

## Quick Start

```bash
pip install westquant[qiskit]
```

Then:

```python
from westquant import optimize

result = optimize(circuit, framework="qiskit", backend=backend, budget=64)
print(result.pareto_front)
```

Or from the command line:

```bash
westquant doctor          # Check what's installed
westquant compare circuit.qasm  # Compare default vs WestQuant search
westquant plugins        # List available plugins
```

## Packages

| Package | Status | Description |
|---------|--------|-------------|
| `westquant-core` | SDK_TESTED | Core contracts, WQIR, RepGraph |
| `westquant-qiskit` | SDK_TESTED | Qiskit transpiler stage plugins |
| `westquant-pytket` | SDK_TESTED | pytket compiler pass search |
| `westquant-pennylane` | SDK_TESTED | PennyLane transform search |
| `westquant-pulser` | SDK_TESTED | Pulser neutral-atom search |
| `westquant-orchestrator` | SDK_TESTED | Cross-framework normalization |
| `westquant-bridges` | EXPERIMENTAL | Cirq/Braket/QIR/OpenQASM bridges |

## Installation

```bash
# Single framework
pip install westquant[qiskit]
pip install westquant[pytket]
pip install westquant[pennylane]
pip install westquant[pulser]

# Everything
pip install westquant[all]
```

## Compare

```bash
westquant compare circuit.qasm -f qiskit
```

Output:
```
                      2Q gates   depth    verified
Qiskit default         143       212       yes
Qiskit opt-3           128       195       yes
WestQuant search       113       179       yes

Candidates evaluated: 64
Verification: EXACT
2Q gate reduction: 20.9%
Depth reduction: 15.6%
```

## Architecture

```
WestQuant Open
├── westquant-core          # WQIR, RepGraph, search contracts
├── westquant-qiskit        # Qiskit transpiler plugins
├── westquant-pytket        # pytket pass search
├── westquant-pennylane     # PennyLane transform search
├── westquant-pulser        # Pulser neutral-atom search
├── westquant-orchestrator  # Cross-framework normalization
├── westquant-bridges       # Experimental framework bridges
└── westquant               # Umbrella package (this repo)
```

## Verification

Every transformation is independently verified:
- **EXACT**: Unitary equivalence via `Operator.equiv()`
- **UNKNOWN**: Conservative — never promoted to EXACT
- **same_problem_different_dynamics**: Pulser-specific — never collapsed with EXACT

## License

Apache-2.0
