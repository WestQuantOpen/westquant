# WQBench data engine foundation

An additive, stricter path than the legacy `generate_training_data` API. Version 0.1 is a validated compilation/provenance foundation, not the complete six-task benchmark or an evaluation of WQT50M.

## Run locally

Python 3.12 and Qiskit 2.6.1 were used for the verified smoke campaign. From this repository:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install 'qiskit==2.6.1' 'pytest==9.1.1'
PYTHONPATH=src python -m westquant.wqbench --dry-run
PYTHONPATH=src python -m westquant.wqbench --db smoke.sqlite --export smoke_export
PYTHONPATH=src python -m westquant.wqbench --db smoke.sqlite --export smoke_export
PYTHONPATH=src python -m pytest tests -q
```

The 12 source circuits belong to 10 root groups: GHZ angle variants share lineage. The second unchanged campaign uses the 192 cached records. Existing failures are cached too; changing the environment/config creates different IDs. No retry overwrites earlier records. SQLite primary keys prevent duplicate rows; parallel writers/retry policy/timeout handling are not implemented in this first serial runner.

Exports are normalized `circuits.jsonl`, `backends.jsonl`, `runs.jsonl`; requested formats are never silently replaced. QASM3 source and output are retained. Fixed root IDs control a deterministic 80/10/10 hash split (small datasets need not have those exact proportions). This is one IID split, not implementations of S1–S5. Caller-provided root IDs must reflect actual common lineage; the library cannot discover all semantic/permutation duplicates. Exact duplicate indexed representations registered with different roots raise an error.

```python
from qiskit import QuantumCircuit
from westquant.wqbench import Engine, TargetSpec

circuit = QuantumCircuit(4)
circuit.h(0)
circuit.cx(0, 3)
with Engine('experiment.sqlite') as engine:
    record, cache_hit = engine.compile(
        circuit,
        root_id='my-independent-problem-001',
        family='my_family',
        target_spec=TargetSpec('synthetic-line-4', 4),
        optimization_level=3,
        seed=101,
    )
    print(record['status'], record['verification'], cache_hit)
    engine.export('experiment_export')
```

Synthetic profiles are configurable. Every change is hashed into the backend ID. Errors and durations are consumed by the explicit Target and metric calculation, not by an actual noise simulator. No real calibration or fidelity measurement is claimed. `gate_time_sum_seconds` is a sum, not scheduled makespan; `independent_gate_success_proxy` is a product proxy, not state fidelity, task success or readout mitigation.

Verification is a full layout-corrected operator check for unitary circuits up to eight qubits with matching source/output widths. Extra target ancillas, larger circuits, measurements/reset and control flow remain UNKNOWN. The target gate set and directed coupling constraints are checked separately. `eligible_for_exact_training` is false for all non-success and non-EXACT records. Structural metrics can be retained for UNKNOWN cases, but should not be relabeled as certified transformations.

Hashing is exact representation identity with fixed qubit indices and numeric parameters. It does not canonicalize arbitrary commuting instructions, qubit permutations, or semantically equivalent circuits. `root_id` is the separate provenance grouping key. Do not confuse content identity with equivalence or statistical independence.

## Scope and next implementation

Implemented: explicit synthetic targets, source/output IDs and QASM, raw metrics, structured failures, conservative equivalence, target validation, root split, deterministic tasks, SQLite resume, normalized JSONL, unit/regression tests.

Next: audit/import the actual WQT50M raw data; manifest/schema validation and Parquet/Croissant; held-out family/backend/size/calibration manifests; true transition/state graphs and the actual twelve action definitions; worker isolation/timeouts/parallelism; scheduling and measured calibration adapters; objective views/Pareto analysis; large-circuit verification and nonunitary semantic checks; predeclared hardware evaluation. None of those is claimed completed here.

Publication decisions and access to private data remain separate. No remote hardware jobs, model training, public release or model-card changes are made by this module. See PLAN_v0_1.md and AUDIT.md.
