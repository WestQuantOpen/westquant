"""WestQuant Dataset Format (WQDF) v0.1.

A standard format for quantum ML training data. Each sample represents
one (problem, representation, circuit, backend, result) tuple.

Schema version: wqdf-v0.1
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import json


WQDF_VERSION = "wqdf-v0.1"


@dataclass
class WQDFSample:
    """One sample in a WestQuant Dataset Format dataset."""
    
    # Problem representation
    problem: str = ""                    # e.g. "maxcut", "qaoa", "vqe"
    problem_representation: dict[str, Any] = field(default_factory=dict)
    
    # Algorithm representation
    algorithm: str = ""                 # e.g. "qaoa_p1", "vqe_twolocal"
    algorithm_representation: dict[str, Any] = field(default_factory=dict)
    
    # Circuit representation
    circuit: str = ""                   # QASM or serialized circuit
    circuit_representation: dict[str, Any] = field(default_factory=dict)
    
    # Compilation representation
    representation: str = ""             # e.g. "qiskit:sabre:opt3"
    compilation_config: dict[str, Any] = field(default_factory=dict)
    
    # Hardware representation
    backend: str = ""                   # e.g. "aer", "ibm_kyoto"
    hardware_representation: dict[str, Any] = field(default_factory=dict)
    
    # Circuit metrics
    num_qubits: int = 0
    depth: int = 0
    two_qubit_gates: int = 0
    size: int = 0
    swap_gates: int = 0
    
    # Noise model
    noise_model: str = ""               # e.g. "depolarizing_0.01"
    
    # Result metrics
    energy: float | None = None
    fidelity: float | None = None
    runtime: float | None = None
    
    # Cost metrics
    estimated_fidelity: float | None = None
    total_duration: float | None = None
    
    # Optimization trajectory
    optimization_trajectory: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    schema_version: str = WQDF_VERSION
    sample_id: str = ""
    framework: str = ""                  # "qiskit", "pytket", "pennylane", "pulser"
    
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = WQDF_VERSION
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WQDFSample":
        d = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**d)


def write_wqdf_jsonl(samples: list[WQDFSample], path: str) -> int:
    """Write samples as WQDF JSONL. Returns number written."""
    with open(path, "w") as f:
        for s in samples:
            f.write(s.to_json() + "\n")
    return len(samples)


def read_wqdf_jsonl(path: str) -> list[WQDFSample]:
    """Read WQDF JSONL file."""
    samples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(WQDFSample.from_dict(json.loads(line)))
    return samples


def wqdf_schema() -> dict[str, Any]:
    """Return the WQDF v0.1 schema as a dict."""
    return {
        "schema_version": WQDF_VERSION,
        "description": "WestQuant Dataset Format for quantum ML training data",
        "fields": {
            "problem": {"type": "str", "description": "Problem class (e.g. maxcut, qaoa, vqe)"},
            "problem_representation": {"type": "dict", "description": "Problem-specific representation data"},
            "algorithm": {"type": "str", "description": "Algorithm name"},
            "algorithm_representation": {"type": "dict", "description": "Algorithm-specific data"},
            "circuit": {"type": "str", "description": "Serialized circuit (QASM)"},
            "circuit_representation": {"type": "dict", "description": "Circuit metrics and structure"},
            "representation": {"type": "str", "description": "Compilation representation ID"},
            "compilation_config": {"type": "dict", "description": "Compiler configuration"},
            "backend": {"type": "str", "description": "Target backend"},
            "hardware_representation": {"type": "dict", "description": "Hardware-specific data"},
            "num_qubits": {"type": "int", "description": "Number of qubits"},
            "depth": {"type": "int", "description": "Circuit depth"},
            "two_qubit_gates": {"type": "int", "description": "Two-qubit gate count"},
            "size": {"type": "int", "description": "Total gate count"},
            "swap_gates": {"type": "int", "description": "SWAP gate count"},
            "noise_model": {"type": "str", "description": "Noise model identifier"},
            "energy": {"type": "float|None", "description": "Measured/computed energy"},
            "fidelity": {"type": "float|None", "description": "State fidelity"},
            "runtime": {"type": "float|None", "description": "Execution time in seconds"},
            "estimated_fidelity": {"type": "float|None", "description": "Estimated circuit fidelity"},
            "total_duration": {"type": "float|None", "description": "Total circuit duration"},
            "optimization_trajectory": {"type": "list[dict]", "description": "Optimization steps"},
            "sample_id": {"type": "str", "description": "Unique sample identifier"},
            "framework": {"type": "str", "description": "Quantum framework used"},
        }
    }
