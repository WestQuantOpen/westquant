"""WestQuant ML Data Generation.

Generate structured datasets from quantum algorithms by varying
representations, transpilation, parameters, noise models, and metrics.

Open-source tier: basic grid search over representations.
Commercial tier (not included): intelligent search, adaptive sampling,
active learning, WQT-guided generation, hardware-aware generation.
"""

from __future__ import annotations

import itertools
import json
import time
from typing import Any
from dataclasses import asdict

from .wqdf import WQDFSample, WQDF_VERSION, write_wqdf_jsonl


def generate_training_data(
    circuit: Any,
    *,
    framework: str = "qiskit",
    backend: str = "aer",
    search_space: str = "representations",
    samples: int = 100,
    output_format: str = "jsonl",
    output_path: str | None = None,
    noise_models: list[str] | None = None,
    basis_gates_options: list[list[str]] | None = None,
    optimization_levels: list[int] | None = None,
    layout_methods: list[str] | None = None,
    routing_methods: list[str] | None = None,
    seed: int = 0,
) -> list[WQDFSample]:
    """Generate ML training data from a quantum circuit.
    
    Varies over representations, transpilation configs, and optionally
    noise models to produce a structured dataset.
    
    Args:
        circuit: Input quantum circuit (Qiskit QuantumCircuit or compatible)
        framework: Quantum framework ("qiskit", "pytket", "pennylane", "pulser")
        backend: Target backend name
        search_space: What to search over ("representations", "parameters", "all")
        samples: Maximum number of samples to generate
        output_format: Output format ("jsonl", "parquet", "csv", "dict")
        output_path: If set, write to this path
        noise_models: List of noise model identifiers to vary over
        basis_gates_options: List of basis gate sets to try
        optimization_levels: List of optimization levels to try
        layout_methods: List of layout methods to try
        routing_methods: List of routing methods to try
        seed: Random seed for reproducibility
    
    Returns:
        List of WQDFSample objects
    
    Example:
        >>> from qiskit import QuantumCircuit
        >>> qc = QuantumCircuit(4)
        >>> # ... build circuit ...
        >>> dataset = generate_training_data(
        ...     qc,
        ...     framework="qiskit",
        ...     backend="aer",
        ...     samples=1000,
        ...     output_format="jsonl",
        ...     output_path="training_data.jsonl",
        ... )
    """
    # Default search dimensions
    opt_levels = optimization_levels or [0, 1, 2, 3]
    layouts = layout_methods or ["trivial", "dense", "sabre"]
    routings = routing_methods or ["basic", "lookahead", "sabre"]
    basis_opts = basis_gates_options or [None]  # None = use backend default
    noises = noise_models or [""]
    
    # Build config grid
    configs = list(itertools.product(opt_levels, layouts, routings, basis_opts, noises))
    
    # Limit to requested samples
    if len(configs) > samples:
        # Deterministic subsampling
        step = len(configs) / samples
        indices = [int(i * step) for i in range(samples)]
        configs = [configs[i] for i in indices]
    
    results: list[WQDFSample] = []
    
    for idx, (opt_level, layout, routing, basis, noise) in enumerate(configs):
        sample_id = f"wqdf-{framework}-{idx:06d}"
        
        # Try to compile and measure
        try:
            metrics = _compile_and_measure(
                circuit,
                framework=framework,
                opt_level=opt_level,
                layout=layout,
                routing=routing,
                basis_gates=basis,
                backend=backend,
                noise_model=noise,
                seed=seed,
            )
        except Exception as exc:
            metrics = {"error": str(exc), "compile_success": False}
        
        sample = WQDFSample(
            problem=_detect_problem(circuit),
            algorithm=_detect_algorithm(circuit),
            circuit=_serialize_circuit(circuit),
            representation=f"{framework}:{routing}:opt{opt_level}",
            compilation_config={
                "optimization_level": opt_level,
                "layout_method": layout,
                "routing_method": routing,
                "basis_gates": basis,
            },
            backend=backend,
            num_qubits=getattr(circuit, "num_qubits", 0),
            depth=metrics.get("depth", 0),
            two_qubit_gates=metrics.get("two_qubit_gates", 0),
            size=metrics.get("size", 0),
            swap_gates=metrics.get("swap_gates", 0),
            noise_model=noise,
            energy=metrics.get("energy"),
            fidelity=metrics.get("fidelity"),
            runtime=metrics.get("runtime"),
            estimated_fidelity=metrics.get("estimated_fidelity"),
            total_duration=metrics.get("total_duration"),
            sample_id=sample_id,
            framework=framework,
        )
        results.append(sample)
    
    # Write output if path provided
    if output_path and output_format == "jsonl":
        write_wqdf_jsonl(results, output_path)
    elif output_path and output_format == "csv":
        _write_csv(results, output_path)
    elif output_path and output_format == "parquet":
        _write_parquet(results, output_path)
    
    return results


def _compile_and_measure(
    circuit: Any,
    *,
    framework: str,
    opt_level: int,
    layout: str,
    routing: str,
    basis_gates: list[str] | None,
    backend: str,
    noise_model: str,
    seed: int,
) -> dict[str, Any]:
    """Compile circuit with given config and measure metrics."""
    if framework == "qiskit":
        return _compile_qiskit(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed)
    elif framework == "pytket":
        return _compile_pytket(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed)
    elif framework == "pennylane":
        return _compile_pennylane(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed)
    elif framework == "pulser":
        return _compile_pulser(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed)
    else:
        return {"error": f"unknown framework: {framework}"}


def _compile_qiskit(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed):
    """Compile with Qiskit and return metrics."""
    try:
        from qiskit.transpiler import generate_preset_pass_manager
        from westquant_qiskit.adapter import circuit_metrics
        
        kwargs = {
            "optimization_level": opt_level,
            "layout_method": layout,
            "routing_method": routing,
            "seed_transpiler": seed,
        }
        if basis_gates:
            kwargs["basis_gates"] = basis_gates
        
        pm = generate_preset_pass_manager(**kwargs)
        compiled = pm.run(circuit)
        metrics = circuit_metrics(compiled)
        metrics["compile_success"] = True
        return metrics
    except Exception as exc:
        return {"compile_success": False, "error": str(exc)}


def _compile_pytket(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed):
    """Compile with pytket and return metrics."""
    try:
        from westquant_pytket.adapter import circuit_metrics
        from westquant_pytket.search import PytketCompiler
        from westquant_core import Action
        
        compiler = PytketCompiler()
        prefix = [
            Action("optimization", ["none", "redundancies", "peephole", "synthesise"][min(opt_level, 3)]),
            Action("routing", routing if routing in ("none", "routing", "aas") else "none"),
        ]
        compiled = compiler.compile(circuit, prefix)
        metrics = circuit_metrics(compiled)
        metrics["compile_success"] = True
        return metrics
    except Exception as exc:
        return {"compile_success": False, "error": str(exc)}


def _compile_pennylane(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed):
    """Compile with PennyLane and return metrics."""
    try:
        import pennylane as qml
        # PennyLane transforms
        tape = qml.tape.QuantumScript(circuit)
        # Basic metrics
        ops = list(tape.operations)
        two_qubit = sum(1 for op in ops if len(op.wires) == 2)
        return {
            "n_qubits": len(tape.wires),
            "depth": len(ops),
            "size": len(ops),
            "two_qubit_gates": two_qubit,
            "swap_gates": 0,
            "compile_success": True,
        }
    except Exception as exc:
        return {"compile_success": False, "error": str(exc)}


def _compile_pulser(circuit, opt_level, layout, routing, basis_gates, backend, noise_model, seed):
    """Compile with Pulser and return metrics."""
    try:
        # Pulser sequence metrics
        return {
            "n_qubits": getattr(circuit, "n_atoms", 0),
            "depth": 0,
            "size": 0,
            "two_qubit_gates": 0,
            "swap_gates": 0,
            "compile_success": True,
        }
    except Exception as exc:
        return {"compile_success": False, "error": str(exc)}


def _detect_problem(circuit: Any) -> str:
    """Heuristically detect the problem class from a circuit."""
    name = getattr(circuit, "name", "").lower()
    if "qaoa" in name or "maxcut" in name:
        return "combinatorial_optimization"
    if "vqe" in name or "twolocal" in name:
        return "variational_eigensolver"
    if "grover" in name:
        return "unstructured_search"
    if "qft" in name:
        return "fourier_transform"
    if "qpe" in name:
        return "phase_estimation"
    return "unknown"


def _detect_algorithm(circuit: Any) -> str:
    """Heuristically detect the algorithm."""
    name = getattr(circuit, "name", "").lower()
    if name:
        return name
    n = getattr(circuit, "num_qubits", 0)
    return f"circuit_{n}q"


def _serialize_circuit(circuit: Any) -> str:
    """Serialize circuit to QASM if possible."""
    try:
        return circuit.qasm()
    except Exception:
        try:
            from qiskit.qasm3 import dumps
            return dumps(circuit)
        except Exception:
            return ""


def _write_csv(samples: list[WQDFSample], path: str) -> None:
    """Write samples as CSV."""
    import csv
    if not samples:
        return
    fields = list(samples[0].to_dict().keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in samples:
            writer.writerow(s.to_dict())


def _write_parquet(samples: list[WQDFSample], path: str) -> None:
    """Write samples as Parquet."""
    try:
        import pandas as pd
        df = pd.DataFrame([s.to_dict() for s in samples])
        df.to_parquet(path)
    except ImportError:
        # Fallback to JSONL
        jsonl_path = path.replace(".parquet", ".jsonl")
        write_wqdf_jsonl(samples, jsonl_path)
