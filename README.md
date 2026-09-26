<div align="center">

# WestQuant Open

### Search the representation, not just the parameters.

**Open-source representation-search layer for quantum computing.**

</div>

---

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/westquant)](https://pypi.org/project/westquant/)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
[![Discussions](https://img.shields.io/badge/discussions-join%20us-blue)](https://github.com/orgs/WestQuantOpen/discussions)

</div>

---

WestQuant Open is an open-source representation-search layer for quantum computing. It searches alternative compilation and representation paths across multiple software stacks, while preserving verification and full provenance.

## Quick start

```bash
pip install westquant[qiskit]
```

```python
from westquant import optimize

result = optimize(circuit, framework="qiskit", backend=backend, budget=64)
print(result.pareto_front)
```

Or from the command line:

```bash
westquant doctor                # Check what's installed
westquant compare circuit.qasm  # Compare default vs WestQuant search
westquant plugins               # List available plugins
```

## Packages

### Core

| Package | Description |
|---------|-------------|
| **[westquant-core](https://github.com/WestQuantOpen/westquant-core)** | Framework-neutral WQIR, RepGraph, plugin contracts |
| **[westquant-qcsc](https://github.com/WestQuantOpen/westquant-qcsc)** | Semantic QPU Minimization — analyze where QPU is actually needed |

### Framework integrations

| Package | Description |
|---------|-------------|
| **[westquant-qiskit](https://github.com/WestQuantOpen/westquant-qiskit)** | Qiskit transpiler stage plugins |
| **[westquant-pytket](https://github.com/WestQuantOpen/westquant-pytket)** | pytket compiler pass search |
| **[westquant-pennylane](https://github.com/WestQuantOpen/westquant-pennylane)** | PennyLane transform search |
| **[westquant-pulser](https://github.com/WestQuantOpen/westquant-pulser)** | Pulser neutral-atom search |

### Infrastructure

| Package | Description |
|---------|-------------|
| **[westquant-orchestrator](https://github.com/WestQuantOpen/westquant-orchestrator)** | Cross-framework trace normalization |
| **[westquant-bridges](https://github.com/WestQuantOpen/westquant-bridges)** | Cirq/Braket/QIR/OpenQASM bridges |

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
├── westquant-qcsc          # Semantic QPU Minimization optimizer
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

## Design philosophy

WestQuant asks three questions in order:

1. **Does this operation need to happen?** (Eliminate)
2. **Does it need to be quantum?** (Replace with classical)
3. **Only then: which resource should execute it?** (Schedule)

That ordering is the defining idea of the project.

## Community

- **Discussions:** [Join the conversation](https://github.com/orgs/WestQuantOpen/discussions)
- **Contributing:** See [CONTRIBUTING.md](https://github.com/WestQuantOpen/.github/blob/main/CONTRIBUTING.md)
- **Code of Conduct:** See [CODE_OF_CONDUCT.md](https://github.com/WestQuantOpen/.github/blob/main/CODE_OF_CONDUCT.md)
- **Releases:** Monthly on the last Friday — see [release schedule](https://github.com/WestQuantOpen/.github/blob/main/RELEASE_SCHEDULE.md)

## License

Apache-2.0

## Author

**David Vesterlund** — Vesterlund Ventures / WestQuant Open Source Project
- Email: david@vesterlundventures.se
- ORCID: [0009-0000-6455-1141](https://orcid.org/0009-0000-6455-1141)
