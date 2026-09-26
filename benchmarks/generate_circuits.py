"""WestQuant Open — Benchmark Circuit Generator

Generates benchmark circuits for 10 algorithm families.
Currently implemented: GHZ, QFT, Grover.

Each circuit is tagged with metadata for reproducibility:
    family, algorithm, n_qubits, instance_id, seed

Usage:
    from benchmarks.generate_circuits import generate_all, generate_family

    # Generate all families
    circuits = generate_all()

    # Generate one family
    circuits = generate_family("ghz", sizes=[4, 6, 8], instances=5)
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate


@dataclass
class BenchmarkCircuit:
    """A single benchmark circuit with metadata."""
    family: str
    algorithm: str
    n_qubits: int
    instance_id: int
    seed: int
    circuit: QuantumCircuit
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def circuit_id(self) -> str:
        """Deterministic ID for this circuit."""
        raw = f"{self.family}:{self.algorithm}:n{self.n_qubits}:i{self.instance_id}:s{self.seed}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def metrics(self) -> dict[str, int]:
        """Return circuit metrics."""
        two_q = sum(1 for inst in self.circuit.data if len(inst.qubits) == 2)
        return {
            "n_qubits": self.circuit.num_qubits,
            "depth": self.circuit.depth(),
            "size": self.circuit.size(),
            "two_qubit_gates": two_q,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata (without circuit object)."""
        return {
            "circuit_id": self.circuit_id,
            "family": self.family,
            "algorithm": self.algorithm,
            "n_qubits": self.n_qubits,
            "instance_id": self.instance_id,
            "seed": self.seed,
            "metrics": self.metrics(),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# GHZ family
# ---------------------------------------------------------------------------

def make_ghz(n_qubits: int, seed: int = 0) -> QuantumCircuit:
    """GHZ state preparation circuit.

    |0>^n -> (|0>^n + |1>^n) / sqrt(2)
    """
    qc = QuantumCircuit(n_qubits, name=f"ghz-{n_qubits}")
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    return qc


def generate_ghz(
    sizes: list[int] | None = None,
    instances: int = 20,
    seed: int = 42,
) -> list[BenchmarkCircuit]:
    """Generate GHZ benchmark circuits.

    Args:
        sizes: Qubit counts to generate (default: 4, 6, 8, 10, ..., 100)
        instances: Number of instances per size (GHZ is deterministic, so
            instances just produces copies with different seeds for downstream
            variation)
        seed: Base random seed
    """
    if sizes is None:
        sizes = list(range(4, 101, 2))  # 4, 6, 8, ..., 100

    circuits = []
    for n in sizes:
        for i in range(instances):
            qc = make_ghz(n, seed=seed + i)
            circuits.append(BenchmarkCircuit(
                family="ghz",
                algorithm="ghz_state_preparation",
                n_qubits=n,
                instance_id=i,
                seed=seed + i,
                circuit=qc,
                metadata={"description": "GHZ state preparation"},
            ))
    return circuits


# ---------------------------------------------------------------------------
# QFT family
# ---------------------------------------------------------------------------

def make_qft(n_qubits: int, seed: int = 0, swaps: bool = True) -> QuantumCircuit:
    """Quantum Fourier Transform circuit.

    Uses Qiskit's QFTGate (the current, non-deprecated API).
    """
    qc = QuantumCircuit(n_qubits, name=f"qft-{n_qubits}")
    qc.append(QFTGate(n_qubits), range(n_qubits))
    return qc.decompose(reps=3)


def generate_qft(
    sizes: list[int] | None = None,
    instances: int = 30,
    seed: int = 42,
) -> list[BenchmarkCircuit]:
    """Generate QFT benchmark circuits.

    Args:
        sizes: Qubit counts (default: 3, 4, 5, ..., 30)
        instances: Instances per size
        seed: Base random seed
    """
    if sizes is None:
        sizes = list(range(3, 31))  # 3, 4, 5, ..., 30

    circuits = []
    for n in sizes:
        for i in range(instances):
            qc = make_qft(n, seed=seed + i)
            circuits.append(BenchmarkCircuit(
                family="qft",
                algorithm="quantum_fourier_transform",
                n_qubits=n,
                instance_id=i,
                seed=seed + i,
                circuit=qc,
                metadata={"description": "QFT using QFTGate", "swaps": True},
            ))
    return circuits


# ---------------------------------------------------------------------------
# Grover family
# ---------------------------------------------------------------------------

def make_grover(n_qubits: int, iterations: int = 1, seed: int = 0) -> QuantumCircuit:
    """Grover's algorithm circuit.

    Builds a simple Grover circuit with a phase oracle that marks the |0...0> state.
    The number of iterations controls the circuit depth (more iterations = more gates).
    """
    qc = QuantumCircuit(n_qubits, name=f"grover-{n_qubits}-{iterations}")
    # Initial superposition
    qc.h(range(n_qubits))

    # Build a simple oracle: mark |0...0> with a phase flip
    # Oracle: multi-controlled Z (using decompose to get standard gates)
    oracle = QuantumCircuit(n_qubits, name="oracle")
    # Mark |0...0>: apply X to all, then MCX, then X to all
    oracle.x(range(n_qubits))
    # Multi-controlled Z = H on target + MCX + H on target
    if n_qubits > 1:
        oracle.h(n_qubits - 1)
        oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        oracle.h(n_qubits - 1)
    else:
        oracle.z(0)
    oracle.x(range(n_qubits))

    # Diffusion operator (Grover diffusion)
    diffuser = QuantumCircuit(n_qubits, name="diffuser")
    diffuser.h(range(n_qubits))
    diffuser.x(range(n_qubits))
    if n_qubits > 1:
        diffuser.h(n_qubits - 1)
        diffuser.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        diffuser.h(n_qubits - 1)
    else:
        diffuser.z(0)
    diffuser.x(range(n_qubits))
    diffuser.h(range(n_qubits))

    # Apply Grover iterations
    for _ in range(iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffuser, inplace=True)

    return qc.decompose(reps=2)


def generate_grover(
    sizes: list[int] | None = None,
    instances: int = 20,
    seed: int = 42,
    max_iterations: int = 3,
) -> list[BenchmarkCircuit]:
    """Generate Grover benchmark circuits.

    Args:
        sizes: Qubit counts (default: 3, 4, 5, ..., 20)
        instances: Instances per size
        seed: Base random seed
        max_iterations: Maximum Grover iterations per circuit
    """
    if sizes is None:
        sizes = list(range(3, 21))  # 3, 4, 5, ..., 20

    circuits = []
    for n in sizes:
        # Vary the number of iterations across instances
        for i in range(instances):
            iterations = (i % max_iterations) + 1
            qc = make_grover(n, iterations=iterations, seed=seed + i)
            circuits.append(BenchmarkCircuit(
                family="grover",
                algorithm="grovers_algorithm",
                n_qubits=n,
                instance_id=i,
                seed=seed + i,
                circuit=qc,
                metadata={
                    "description": "Grover's algorithm",
                    "iterations": iterations,
                },
            ))
    return circuits


# ---------------------------------------------------------------------------
# Master generator
# ---------------------------------------------------------------------------

FAMILY_GENERATORS = {
    "ghz": generate_ghz,
    "qft": generate_qft,
    "grover": generate_grover,
}


def generate_family(
    family: str,
    sizes: list[int] | None = None,
    instances: int = 20,
    seed: int = 42,
) -> list[BenchmarkCircuit]:
    """Generate benchmark circuits for one family."""
    gen = FAMILY_GENERATORS.get(family)
    if gen is None:
        raise ValueError(f"Unknown family: {family}. Available: {list(FAMILY_GENERATORS)}")
    return gen(sizes=sizes, instances=instances, seed=seed)


def generate_all(
    families: list[str] | None = None,
    sizes: list[int] | None = None,
    instances: int = 20,
    seed: int = 42,
) -> list[BenchmarkCircuit]:
    """Generate benchmark circuits for all implemented families.

    Args:
        families: Which families to generate (default: all implemented)
        sizes: Override default sizes for all families
        instances: Instances per size per family
        seed: Base random seed

    Returns:
        List of BenchmarkCircuit objects
    """
    if families is None:
        families = list(FAMILY_GENERATORS.keys())

    all_circuits = []
    for family in families:
        circuits = generate_family(family, sizes=sizes, instances=instances, seed=seed)
        all_circuits.extend(circuits)
    return all_circuits


def save_manifest(circuits: list[BenchmarkCircuit], path: str) -> None:
    """Save a manifest of circuit metadata (without circuit objects)."""
    manifest = [c.to_dict() for c in circuits]
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate WestQuant benchmark circuits")
    parser.add_argument("--family", type=str, default="all",
                        help="Circuit family (ghz, qft, grover, all)")
    parser.add_argument("--sizes", type=int, nargs="+", default=None,
                        help="Qubit sizes to generate")
    parser.add_argument("--instances", type=int, default=20,
                        help="Instances per size")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--manifest", type=str, default="benchmarks/circuits/manifest.json",
                        help="Output manifest path")
    args = parser.parse_args()

    if args.family == "all":
        circuits = generate_all(sizes=args.sizes, instances=args.instances, seed=args.seed)
    else:
        circuits = generate_family(args.family, sizes=args.sizes, instances=args.instances, seed=args.seed)

    save_manifest(circuits, args.manifest)

    # Print summary
    print(f"\nGenerated {len(circuits)} benchmark circuits")
    by_family = {}
    for c in circuits:
        by_family.setdefault(c.family, []).append(c)

    for family, fam_circuits in sorted(by_family.items()):
        sizes = sorted(set(c.n_qubits for c in fam_circuits))
        print(f"  {family:10s}: {len(fam_circuits):4d} circuits, sizes {sizes}")

    print(f"\nManifest saved to: {args.manifest}")
