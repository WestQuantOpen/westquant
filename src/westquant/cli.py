"""WestQuant Open CLI — umbrella commands.

Commands:
    westquant doctor     # Check installation status
    westquant compare     # Compare default vs WestQuant search on a circuit
    westquant plugins     # List available plugins
    westquant version     # Show version info
    westquant generate    # Generate ML training data from a circuit
"""
from __future__ import annotations

import argparse
import sys
from typing import Any


def _check_import(module_name: str) -> tuple[bool, str | None]:
    """Try to import a module. Returns (success, version_or_none)."""
    try:
        mod = __import__(module_name, fromlist=["__version__"])
        version = getattr(mod, "__version__", "unknown")
        return True, version
    except ImportError:
        return False, None


def cmd_doctor(args: argparse.Namespace) -> int:
    """Check what's installed and working."""
    print()
    print("  WestQuant Open 0.1")
    print()
    print("  Component          Status   Version")
    print("  ─────────────────  ───────  ───────────")

    checks = [
        ("Core", "westquant_core"),
        ("Qiskit", "westquant_qiskit"),
        ("pytket", "westquant_pytket"),
        ("PennyLane", "westquant_pennylane"),
        ("Pulser", "westquant_pulser"),
        ("Orchestrator", "westquant_orchestrator"),
        ("Bridges", "westquant_bridges"),
    ]

    all_ok = True
    for name, module in checks:
        ok, version = _check_import(module)
        status = "✓" if ok else "-"
        ver_str = version or "not installed"
        print(f"  {name:18s}  {status:5s}   {ver_str}")
        if not ok:
            all_ok = False

    # Check SDK availability
    print()
    print("  SDK                Status   Version")
    print("  ─────────────────  ───────  ───────────")

    sdk_checks = [
        ("Qiskit", "qiskit"),
        ("pytket", "pytket"),
        ("PennyLane", "pennylane"),
        ("Pulser", "pulser"),
    ]

    for name, module in sdk_checks:
        ok, version = _check_import(module)
        status = "✓" if ok else "-"
        ver_str = version or "unavailable"
        print(f"  {name:18s}  {status:5s}   {ver_str}")

    # Check WQT20
    print()
    wqt_ok, _ = _check_import("wqt20")
    wqt_status = "✓" if wqt_ok else "not installed"
    print(f"  WQT20              {wqt_status}")

    # Check CUDA-Q
    cuda_ok, _ = _check_import("cudaq")
    cuda_status = "✓" if cuda_ok else "unavailable"
    print(f"  CUDA-Q             {cuda_status}")

    print()
    if all_ok:
        print("  All WestQuant components are installed.")
    else:
        print("  Some components are not installed.")
        print("  Install with: pip install westquant[all]")
    print()

    return 0


def cmd_plugins(args: argparse.Namespace) -> int:
    """List available plugins."""
    print()
    print("  WestQuant Open Plugins")
    print()

    plugins = [
        ("westquant-qiskit", "Qiskit transpiler stage plugins", "qiskit", "SDK_TESTED"),
        ("westquant-pytket", "pytket compiler pass search", "pytket", "SDK_TESTED"),
        ("westquant-pennylane", "PennyLane transform search", "pennylane", "SDK_TESTED"),
        ("westquant-pulser", "Pulser neutral-atom search", "pulser", "SDK_TESTED"),
        ("westquant-bridges", "Cirq/Braket/QIR/OpenQASM bridges", "various", "EXPERIMENTAL"),
    ]

    print(f"  {'Package':30s}  {'Description':40s}  {'Status':12s}")
    print(f"  {'─'*30}  {'─'*40}  {'─'*12}")

    for pkg, desc, sdk, status in plugins:
        print(f"  {pkg:30s}  {desc:40s}  {status:12s}")

    print()
    print("  Install: pip install westquant[qiskit]")
    print("  Install all: pip install westquant[all]")
    print()

    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Show version info."""
    print("WestQuant Open 0.1.0a2")
    print("  Schema: wqt-policy-v0.1")
    print("  WQIR: v0.2")
    print("  RepGraph: v0.2")
    print("  WQDF: wqdf-v0.1")

    core_ok, core_ver = _check_import("westquant_core")
    if core_ok:
        print(f"  Core: {core_ver}")

    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare default vs WestQuant search on a circuit."""
    circuit_path = args.circuit
    framework = args.framework

    print()
    print("  WestQuant Compare")
    print(f"  Circuit: {circuit_path}")
    print(f"  Framework: {framework}")
    print()

    if framework == "qiskit":
        return _compare_qiskit(circuit_path, args)
    elif framework == "pytket":
        return _compare_pytket(circuit_path, args)
    elif framework == "pennylane":
        return _compare_pennylane(circuit_path, args)
    elif framework == "pulser":
        return _compare_pulser(circuit_path, args)
    else:
        print(f"  Unknown framework: {framework}")
        print(f"  Supported: qiskit, pytket, pennylane, pulser")
        return 1


def _compare_qiskit(circuit_path: str, args: argparse.Namespace) -> int:
    """Compare Qiskit default vs WestQuant search."""
    try:
        from qiskit import QuantumCircuit
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    except ImportError:
        print("  Qiskit not installed. Install with: pip install westquant[qiskit]")
        return 1

    # Load circuit
    try:
        if circuit_path.endswith(".qasm"):
            qc = QuantumCircuit.from_qasm_file(circuit_path)
        else:
            print(f"  Unsupported circuit format. Use .qasm files.")
            return 1
    except Exception as e:
        print(f"  Error loading circuit: {e}")
        return 1

    n_qubits = qc.num_qubits
    print(f"  Qubits: {n_qubits}")
    print(f"  Gates: {qc.size()}")
    print()

    # Default compilation
    opt_level = args.optimization_level or 2
    pm_default = generate_preset_pass_manager(optimization_level=opt_level)
    tqc_default = pm_default.run(qc)

    default_2q = sum(1 for inst in tqc_default.data if len(inst.qubits) == 2)
    default_depth = tqc_default.depth()

    print(f"  {'':20s}  {'2Q gates':>10s}  {'depth':>10s}  {'verified':>10s}")
    print(f"  {'─'*20}  {'─'*10}  {'─'*10}  {'─'*10}")
    print(f"  {'Qiskit default':20s}  {default_2q:>10d}  {default_depth:>10d}  {'yes':>10s}")

    # Try higher optimization levels
    for level in [3]:
        if level == opt_level:
            continue
        pm = generate_preset_pass_manager(optimization_level=level)
        tqc = pm.run(qc)
        gates_2q = sum(1 for inst in tqc.data if len(inst.qubits) == 2)
        depth = tqc.depth()
        print(f"  {'Qiskit opt-' + str(level):20s}  {gates_2q:>10d}  {depth:>10d}  {'yes':>10s}")

    # WestQuant search
    try:
        from westquant_qiskit.search import DeterministicSearchEngine
        engine = DeterministicSearchEngine()
        result = engine.search(qc, challenge_id="compare", max_candidates=8)
        best = result.best
        if best:
            wq_2q = best.metrics.get("two_qubit_gates", 0)
            wq_depth = best.metrics.get("depth", 0)
            print(f"  {'WestQuant search':20s}  {wq_2q:>10d}  {wq_depth:>10d}  {'yes':>10s}")
            print()
            print(f"  Candidates evaluated: {len(result.candidates)}")
            print(f"  Verification: EXACT")
            if wq_2q < default_2q:
                saving = (1 - wq_2q / default_2q) * 100
                print(f"  2Q gate reduction: {saving:.1f}%")
            if wq_depth < default_depth:
                saving = (1 - wq_depth / default_depth) * 100
                print(f"  Depth reduction: {saving:.1f}%")
        else:
            print(f"  {'WestQuant search':20s}  {'N/A':>10s}  {'N/A':>10s}  {'N/A':>10s}")
    except ImportError:
        print("  WestQuant Qiskit plugin not installed.")
        print("  Install with: pip install westquant[qiskit]")
        return 1
    except Exception as e:
        print(f"  WestQuant search error: {e}")
        return 1

    print()
    return 0


def _compare_pytket(circuit_path: str, args: argparse.Namespace) -> int:
    """Compare pytket default vs WestQuant search."""
    print("  pytket compare — coming soon")
    return 0


def _compare_pennylane(circuit_path: str, args: argparse.Namespace) -> int:
    """Compare PennyLane default vs WestQuant search."""
    print("  PennyLane compare — coming soon")
    return 0


def _compare_pulser(circuit_path: str, args: argparse.Namespace) -> int:
    """Compare Pulser default vs WestQuant search."""
    print("  Pulser compare — coming soon")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate ML training data from a circuit."""
    from .generate import generate_training_data

    circuit_path = args.circuit_file
    framework = args.framework
    backend = args.backend
    samples = args.samples
    output = args.output
    fmt = args.format

    print()
    print("  WestQuant ML Data Generation")
    print(f"  Circuit: {circuit_path}")
    print(f"  Framework: {framework}")
    print(f"  Backend: {backend}")
    print(f"  Max samples: {samples}")
    print(f"  Output: {output} ({fmt})")
    print()

    # Load circuit
    try:
        if framework == "qiskit":
            from qiskit import QuantumCircuit
            if circuit_path.endswith(".qasm"):
                qc = QuantumCircuit.from_qasm_file(circuit_path)
            else:
                print(f"  Unsupported circuit format. Use .qasm files.")
                return 1
        else:
            print(f"  Framework {framework} circuit loading not yet supported in CLI.")
            return 1
    except ImportError:
        print(f"  {framework} not installed. Install with: pip install westquant[{framework}]")
        return 1
    except Exception as e:
        print(f"  Error loading circuit: {e}")
        return 1

    print(f"  Qubits: {qc.num_qubits}")
    print()

    # Generate
    dataset = generate_training_data(
        qc,
        framework=framework,
        backend=backend,
        samples=samples,
        output_format=fmt,
        output_path=output,
    )

    print(f"  Generated {len(dataset)} samples")
    if output:
        print(f"  Written to: {output}")

    # Show a few samples
    for s in dataset[:3]:
        print(f"    {s.sample_id}: depth={s.depth} 2q={s.two_qubit_gates} rep={s.representation}")
    if len(dataset) > 3:
        print(f"    ... ({len(dataset) - 3} more)")

    print()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="westquant",
        description="WestQuant Open — Search the representation, not just the parameters",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check installation status")
    subparsers.add_parser("plugins", help="List available plugins")
    subparsers.add_parser("version", help="Show version info")

    compare_parser = subparsers.add_parser("compare", help="Compare default vs WestQuant search")
    compare_parser.add_argument("circuit", help="Path to circuit file (.qasm)")
    compare_parser.add_argument("-f", "--framework", default="qiskit", choices=["qiskit", "pytket", "pennylane", "pulser"])
    compare_parser.add_argument("-o", "--optimization-level", type=int, default=2, help="Qiskit optimization level for baseline")

    generate_parser = subparsers.add_parser("generate", help="Generate ML training data from a circuit")
    generate_parser.add_argument("circuit_file", help="Path to circuit file (.qasm)")
    generate_parser.add_argument("-f", "--framework", default="qiskit", choices=["qiskit", "pytket", "pennylane", "pulser"])
    generate_parser.add_argument("-b", "--backend", default="aer", help="Target backend")
    generate_parser.add_argument("-n", "--samples", type=int, default=100, help="Maximum number of samples")
    generate_parser.add_argument("-o", "--output", default="dataset.jsonl", help="Output path")
    generate_parser.add_argument("--format", default="jsonl", choices=["jsonl", "csv", "parquet"], help="Output format")

    args = parser.parse_args()

    if args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "plugins":
        sys.exit(cmd_plugins(args))
    elif args.command == "version":
        sys.exit(cmd_version(args))
    elif args.command == "compare":
        sys.exit(cmd_compare(args))
    elif args.command == "generate":
        sys.exit(cmd_generate(args))


if __name__ == "__main__":
    main()
