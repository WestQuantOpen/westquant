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
from westquant_qiskit.search import DeterministicSearchEngine

result = DeterministicSearchEngine().search(circuit, challenge_id="demo", backend=backend, max_candidates=64)
print(result.best.metrics, result.best.verification.equivalence)
print([c.metrics for c in result.pareto_front])
```

The umbrella package itself exports the WQDF dataset helpers
(`from westquant import generate_training_data, WQDFSample`).

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

Actual output for a 5-qubit QFT (westquant 0.1.1, Qiskit 2.6.1, no target):
```
                          2Q gates       depth  verification
  ────────────────────  ──────────  ──────────  ────────────
  Qiskit opt-2 (base)           26          29         exact
  Qiskit opt-3                  26          29         exact
  WestQuant search              26          34         exact

  Candidates evaluated: 8 (8 verified exact)
  Verification of selected candidate: exact
```

The verification column is the status returned by `QiskitEquivalenceVerifier`
for that exact circuit: `exact`, `invalid` or `unknown`. Circuits with
measurements, resets or more than 8 qubits are reported as `unknown`, and
reductions are then not printed. Only `-f qiskit` is implemented; other
frameworks exit with status 2.

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

Every candidate carries an explicit verification status:
- **EXACT**: Unitary equivalence via `Operator.equiv()` (small, unitary circuits)
- **UNKNOWN**: Conservative — not checked or not checkable; never promoted to EXACT
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
