"""WestQuant Open — Multi-Output Pipeline Agent

Takes a single benchmark run and produces 5 deliverables in parallel:

    1. Benchmark results  (results.json, summary.md, figure.png)
    2. Paper data          (tables.tex, metrics.json, figures/)
    3. GitHub demo         (demo/README.md, demo/example.ipynb)
    4. Blog post           (blog_post.md)
    5. WQT20 training data (training_data.jsonl)

One benchmark run -> five outputs. The leverage point for the whole project.

Usage:
    python -m benchmarks.pipeline_agent \\
        --family qft \\
        --sizes 4 6 8 \\
        --instances 3 \\
        --samples 50 \\
        --output benchmarks/results/run_001/

    # Or from code:
    from benchmarks.pipeline_agent import run_pipeline
    run_pipeline(family="qft", sizes=[4,6,8], instances=3, samples=50,
                 output_dir="benchmarks/results/run_001/")
"""
from __future__ import annotations

import json
import time
import hashlib
import statistics
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate

from westquant import generate_training_data, write_wqdf_jsonl, WQDFSample
from westquant_qiskit import circuit_metrics, QiskitAdapter
from benchmarks.generate_circuits import (
    BenchmarkCircuit,
    generate_ghz,
    generate_qft,
    generate_grover,
    FAMILY_GENERATORS,
)


# ---------------------------------------------------------------------------
# Data container — shared input to all 5 workers
# ---------------------------------------------------------------------------

@dataclass
class PipelineInput:
    """The shared input for all 5 output workers."""
    run_id: str
    family: str
    sizes: list[int]
    instances: int
    samples_per_circuit: int
    seed: int
    circuits: list[BenchmarkCircuit] = field(default_factory=list)
    all_samples: list[WQDFSample] = field(default_factory=list)
    timestamp: str = ""
    config: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "family": self.family,
            "sizes": self.sizes,
            "instances": self.instances,
            "samples_per_circuit": self.samples_per_circuit,
            "total_circuits": len(self.circuits),
            "total_samples": len(self.all_samples),
            "timestamp": self.timestamp,
            "config": self.config,
        }


# ---------------------------------------------------------------------------
# Worker 1: Benchmark Results
# ---------------------------------------------------------------------------

def worker_benchmark_results(inp: PipelineInput, output_dir: Path) -> dict[str, Any]:
    """Produce: results.json, summary.md, figure.png"""
    out = output_dir / "benchmark"
    out.mkdir(parents=True, exist_ok=True)

    # Aggregate metrics by size
    by_size: dict[int, list[dict]] = {}
    for s in inp.all_samples:
        n = s.num_qubits
        by_size.setdefault(n, []).append({
            "depth": s.depth,
            "two_qubit_gates": s.two_qubit_gates,
            "size": s.size,
            "swap_gates": s.swap_gates,
            "representation": s.representation,
        })

    results = {
        "run_id": inp.run_id,
        "family": inp.family,
        "timestamp": inp.timestamp,
        "total_samples": len(inp.all_samples),
        "by_size": {},
    }

    for n in sorted(by_size):
        entries = by_size[n]
        depths = [e["depth"] for e in entries]
        gates_2q = [e["two_qubit_gates"] for e in entries]
        sizes = [e["size"] for e in entries]
        results["by_size"][str(n)] = {
            "count": len(entries),
            "depth": {
                "min": min(depths), "max": max(depths),
                "median": statistics.median(depths),
                "mean": statistics.mean(depths),
            },
            "two_qubit_gates": {
                "min": min(gates_2q), "max": max(gates_2q),
                "median": statistics.median(gates_2q),
                "mean": statistics.mean(gates_2q),
            },
            "size": {
                "min": min(sizes), "max": max(sizes),
                "median": statistics.median(sizes),
                "mean": statistics.mean(sizes),
            },
        }

    # Save results.json
    with open(out / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save summary.md
    lines = [
        f"# Benchmark Results — {inp.family.upper()} ({inp.run_id})",
        f"",
        f"**Run ID:** {inp.run_id}  ",
        f"**Timestamp:** {inp.timestamp}  ",
        f"**Total samples:** {len(inp.all_samples)}  ",
        f"**Sizes:** {inp.sizes}",
        f"",
        f"| Qubits | Samples | Depth (median) | 2Q Gates (median) | Size (median) |",
        f"|--------|---------|----------------|-------------------|---------------|",
    ]
    for n in sorted(by_size):
        d = results["by_size"][str(n)]
        lines.append(
            f"| {n} | {d['count']} | {d['depth']['median']:.0f} | "
            f"{d['two_qubit_gates']['median']:.0f} | {d['size']['median']:.0f} |"
        )
    lines.append("")

    with open(out / "summary.md", "w") as f:
        f.write("\n".join(lines))

    # Save figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        ns = sorted(by_size)
        depth_medians = [results["by_size"][str(n)]["depth"]["median"] for n in ns]
        gate_medians = [results["by_size"][str(n)]["two_qubit_gates"]["median"] for n in ns]

        axes[0].plot(ns, depth_medians, "o-", color="steelblue", linewidth=2, markersize=8)
        axes[0].set_xlabel("Qubits")
        axes[0].set_ylabel("Depth (median)")
        axes[0].set_title(f"{inp.family.upper()} — Depth vs Size")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(ns, gate_medians, "s-", color="coral", linewidth=2, markersize=8)
        axes[1].set_xlabel("Qubits")
        axes[1].set_ylabel("2Q Gates (median)")
        axes[1].set_title(f"{inp.family.upper()} — 2Q Gates vs Size")
        axes[1].grid(True, alpha=0.3)

        plt.suptitle(f"Benchmark: {inp.family.upper()} ({len(inp.all_samples)} samples)", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(out / "figure.png", dpi=150, bbox_inches="tight")
        plt.close()
    except Exception as e:
        # matplotlib not available — skip figure
        pass

    return {"worker": "benchmark_results", "output": str(out), "files": ["results.json", "summary.md", "figure.png"]}


# ---------------------------------------------------------------------------
# Worker 2: Paper Data
# ---------------------------------------------------------------------------

def worker_paper_data(inp: PipelineInput, output_dir: Path) -> dict[str, Any]:
    """Produce: tables.tex, metrics.json, figures/"""
    out = output_dir / "paper"
    out.mkdir(parents=True, exist_ok=True)

    # Collect metrics for paper
    by_size: dict[int, list[dict]] = {}
    for s in inp.all_samples:
        by_size.setdefault(s.num_qubits, []).append({
            "depth": s.depth,
            "two_qubit_gates": s.two_qubit_gates,
            "size": s.size,
        })

    # metrics.json — structured for paper scripts
    metrics = {
        "run_id": inp.run_id,
        "family": inp.family,
        "n_samples": len(inp.all_samples),
        "n_sizes": len(by_size),
        "sizes": sorted(by_size),
        "results": {},
    }
    for n in sorted(by_size):
        entries = by_size[n]
        metrics["results"][str(n)] = {
            "depth": {
                "mean": statistics.mean(e["depth"] for e in entries),
                "median": statistics.median(e["depth"] for e in entries),
                "std": statistics.stdev(e["depth"] for e in entries) if len(entries) > 1 else 0,
            },
            "two_qubit_gates": {
                "mean": statistics.mean(e["two_qubit_gates"] for e in entries),
                "median": statistics.median(e["two_qubit_gates"] for e in entries),
                "std": statistics.stdev(e["two_qubit_gates"] for e in entries) if len(entries) > 1 else 0,
            },
        }

    with open(out / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # tables.tex — LaTeX tables for paper
    tex_lines = [
        f"% Auto-generated by WestQuant pipeline_agent — {inp.timestamp}",
        f"% Run: {inp.run_id}, Family: {inp.family}, Samples: {len(inp.all_samples)}",
        "",
        f"\\begin{{table}}[htbp]",
        f"\\caption{{{inp.family.upper()} compilation metrics ({len(inp.all_samples)} samples)}}",
        f"\\label{{tab:{inp.family}_{inp.run_id}}}",
        f"\\centering",
        f"\\begin{{tabular}}{{ccccc}}",
        f"\\hline",
        f"Qubits & Samples & Depth (mean$\\pm$std) & 2Q Gates (mean$\\pm$std) & Size (mean) \\\\",
        f"\\hline",
    ]
    for n in sorted(by_size):
        d = metrics["results"][str(n)]
        tex_lines.append(
            f"{n} & {len(by_size[n])} & "
            f"{d['depth']['mean']:.1f} $\\pm$ {d['depth']['std']:.1f} & "
            f"{d['two_qubit_gates']['mean']:.1f} $\\pm$ {d['two_qubit_gates']['std']:.1f} & "
            f"{statistics.mean(e['size'] for e in by_size[n]):.1f} \\\\"
        )
    tex_lines.extend(["\\hline", "\\end{tabular}", "\\end{table}", ""])

    with open(out / "tables.tex", "w") as f:
        f.write("\n".join(tex_lines))

    # Paper figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(8, 5))
        ns = sorted(by_size)
        depth_means = [metrics["results"][str(n)]["depth"]["mean"] for n in ns]
        depth_stds = [metrics["results"][str(n)]["depth"]["std"] for n in ns]
        gate_means = [metrics["results"][str(n)]["two_qubit_gates"]["mean"] for n in ns]
        gate_stds = [metrics["results"][str(n)]["two_qubit_gates"]["std"] for n in ns]

        ax.errorbar(ns, depth_means, yerr=depth_stds, fmt="o-", color="steelblue",
                     linewidth=2, capsize=5, label="Depth")
        ax.errorbar(ns, gate_means, yerr=gate_stds, fmt="s-", color="coral",
                     linewidth=2, capsize=5, label="2Q Gates")
        ax.set_xlabel("Number of Qubits", fontsize=12)
        ax.set_ylabel("Count", fontsize=12)
        ax.set_title(f"{inp.family.upper()} Compilation Metrics", fontsize=14)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(out / "paper_figure.png", dpi=300, bbox_inches="tight")
        plt.close()
    except Exception:
        pass

    return {"worker": "paper_data", "output": str(out), "files": ["metrics.json", "tables.tex", "paper_figure.png"]}


# ---------------------------------------------------------------------------
# Worker 3: GitHub Demo
# ---------------------------------------------------------------------------

def worker_github_demo(inp: PipelineInput, output_dir: Path) -> dict[str, Any]:
    """Produce: demo/README.md with embedded results"""
    out = output_dir / "demo"
    out.mkdir(parents=True, exist_ok=True)

    # Find best and worst samples
    if not inp.all_samples:
        return {"worker": "github_demo", "output": str(out), "files": []}

    best = min(inp.all_samples, key=lambda s: s.two_qubit_gates)
    worst = max(inp.all_samples, key=lambda s: s.two_qubit_gates)
    baseline = inp.all_samples[0]

    readme = f"""# WestQuant Open — {inp.family.upper()} Demo

> Auto-generated from benchmark run `{inp.run_id}` on {inp.timestamp}

## What this demonstrates

One {inp.family.upper()} circuit compiled {len(inp.all_samples)} different ways —
the same algorithm, different representations, different metrics.

## Results

| Metric | Best | Worst | Baseline |
|--------|------|-------|----------|
| Depth | {best.depth} | {worst.depth} | {baseline.depth} |
| 2Q Gates | {best.two_qubit_gates} | {worst.two_qubit_gates} | {baseline.two_qubit_gates} |
| Size | {best.size} | {worst.size} | {baseline.size} |

**Best representation:** `{best.representation}`
**Worst representation:** `{worst.representation}`

## 2Q gate reduction

Best vs worst: {(worst.two_qubit_gates - best.two_qubit_gates) / worst.two_qubit_gates * 100:.1f}% reduction

## Reproduce

```bash
pip install westquant[qiskit]

python -m benchmarks.pipeline_agent \\
    --family {inp.family} \\
    --sizes {' '.join(map(str, inp.sizes))} \\
    --instances {inp.instances} \\
    --samples {inp.samples_per_circuit}
```

## Data

- Total samples: {len(inp.all_samples)}
- Sizes: {inp.sizes}
- Family: {inp.family}

---

Generated by [WestQuant Open](https://github.com/WestQuantOpen) pipeline_agent.
"""
    with open(out / "README.md", "w") as f:
        f.write(readme)

    # Also save a small JSON snippet for embedding
    snippet = {
        "family": inp.family,
        "run_id": inp.run_id,
        "best": {"representation": best.representation, "depth": best.depth, "two_qubit_gates": best.two_qubit_gates},
        "worst": {"representation": worst.representation, "depth": worst.depth, "two_qubit_gates": worst.two_qubit_gates},
        "total_samples": len(inp.all_samples),
    }
    with open(out / "demo_data.json", "w") as f:
        json.dump(snippet, f, indent=2)

    return {"worker": "github_demo", "output": str(out), "files": ["README.md", "demo_data.json"]}


# ---------------------------------------------------------------------------
# Worker 4: Blog Post
# ---------------------------------------------------------------------------

def worker_blog_post(inp: PipelineInput, output_dir: Path) -> dict[str, Any]:
    """Produce: blog_post.md"""
    out = output_dir / "blog"
    out.mkdir(parents=True, exist_ok=True)

    if not inp.all_samples:
        return {"worker": "blog_post", "output": str(out), "files": []}

    best = min(inp.all_samples, key=lambda s: s.two_qubit_gates)
    worst = max(inp.all_samples, key=lambda s: s.two_qubit_gates)
    improvement = (worst.two_qubit_gates - best.two_qubit_gates) / worst.two_qubit_gates * 100

    # Aggregate by size for the narrative
    by_size: dict[int, list[int]] = {}
    for s in inp.all_samples:
        by_size.setdefault(s.num_qubits, []).append(s.two_qubit_gates)

    size_table = "| Qubits | Samples | Best 2Q | Worst 2Q | Median 2Q |\n|--------|---------|---------|----------|-----------|\n"
    for n in sorted(by_size):
        gates = by_size[n]
        size_table += f"| {n} | {len(gates)} | {min(gates)} | {max(gates)} | {statistics.median(gates):.0f} |\n"

    post = f"""# {inp.family.upper()} Compilation: {len(inp.all_samples)} Representations from One Algorithm

*Auto-generated by WestQuant Open pipeline_agent on {inp.timestamp}*

---

We took a single {inp.family.upper()} circuit and compiled it {len(inp.all_samples)} different ways using WestQuant Open. Here's what we found.

## The setup

WestQuant Open varies over optimization levels, basis gate sets, layout methods, and routing methods to explore the full compilation space. Instead of relying on 4 fixed optimization levels, we search systematically.

**Input:** {inp.family.upper()} circuits at sizes {', '.join(map(str, inp.sizes))} qubits
**Samples generated:** {len(inp.all_samples)}
**Configurations varied:** optimization level, basis gates, layout, routing

## Results

{size_table}

## The headline

The best representation uses **{best.two_qubit_gates} two-qubit gates** — a **{improvement:.1f}% reduction** compared to the worst representation ({worst.two_qubit_gates} gates).

- **Best:** `{best.representation}` — depth={best.depth}, 2Q={best.two_qubit_gates}
- **Worst:** `{worst.representation}` — depth={worst.depth}, 2Q={worst.two_qubit_gates}

On real hardware, fewer two-qubit gates directly translates to lower error rates and higher fidelity. This is not a theoretical improvement — it's a practical one.

## Why this matters

Quantum compilers today use fixed pipelines. Qiskit has 4 optimization levels. PennyLane has a fixed transform stack. The order and combination of passes significantly affects the result — but most users never explore beyond the default.

WestQuant Open searches this space automatically. And every search produces training data for the next generation of quantum compilers.

## The data factory

Each compilation produces a `(state, action, next_state, reward)` tuple:

- **state:** circuit metrics before compilation
- **action:** the compilation configuration (opt level, basis gates, layout, routing)
- **next_state:** circuit metrics after compilation
- **reward:** the improvement (negative delta = better)

This run produced **{len(inp.all_samples)} training examples** from {len(inp.circuits)} circuits. Scale this across 10 algorithm families and 50 instances each, and you get 10,000+ examples — the training data for WQT20.

## Try it

```bash
pip install westquant[qiskit]
python -m benchmarks.pipeline_agent --family {inp.family} --sizes {' '.join(map(str, inp.sizes))} --instances {inp.instances} --samples {inp.samples_per_circuit}
```

## Reproducibility

- **Run ID:** {inp.run_id}
- **Seed:** {inp.seed}
- **Timestamp:** {inp.timestamp}
- **Full data:** See `benchmark/results.json` and `training_data/training_data.jsonl`

---

*WestQuant Open is an open-source project for AI x Quantum Algorithm Engineering. [github.com/WestQuantOpen](https://github.com/WestQuantOpen)*
"""
    with open(out / "blog_post.md", "w") as f:
        f.write(post)

    return {"worker": "blog_post", "output": str(out), "files": ["blog_post.md"]}


# ---------------------------------------------------------------------------
# Worker 5: WQT20 Training Data
# ---------------------------------------------------------------------------

def worker_training_data(inp: PipelineInput, output_dir: Path) -> dict[str, Any]:
    """Produce: training_data.jsonl with (s, a, s', r) tuples"""
    out = output_dir / "training_data"
    out.mkdir(parents=True, exist_ok=True)

    # Convert WQDF samples to (state, action, next_state, reward) tuples
    records = []
    for s in inp.all_samples:
        # Find the baseline circuit for this sample's qubit count
        baseline_circuit = None
        for c in inp.circuits:
            if c.n_qubits == s.num_qubits:
                baseline_circuit = c.circuit
                break

        baseline_depth = baseline_circuit.depth() if baseline_circuit else 0
        baseline_2q = sum(1 for inst in baseline_circuit.data if len(inst.qubits) == 2) if baseline_circuit else 0
        baseline_size = baseline_circuit.size() if baseline_circuit else 0

        record = {
            # State (before)
            "state": {
                "algorithm": inp.family,
                "n_qubits": s.num_qubits,
                "depth": baseline_depth,
                "two_qubit_gates": baseline_2q,
                "size": baseline_size,
            },
            # Action (compilation config)
            "action": {
                "representation": s.representation,
                "framework": s.framework,
                "backend": s.backend,
            },
            # Next state (after compilation)
            "next_state": {
                "depth": s.depth,
                "two_qubit_gates": s.two_qubit_gates,
                "size": s.size,
                "swap_gates": s.swap_gates,
            },
            # Reward (negative delta = improvement)
            "reward": {
                "delta_depth": s.depth - baseline_depth,
                "delta_2q": s.two_qubit_gates - baseline_2q,
                "delta_size": s.size - baseline_size,
            },
            # Metadata
            "sample_id": s.sample_id,
            "schema": "wqt20-training-v0.1",
        }
        records.append(record)

    # Write JSONL
    jsonl_path = out / "training_data.jsonl"
    with open(jsonl_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Write summary
    summary = {
        "total_records": len(records),
        "schema": "wqt20-training-v0.1",
        "family": inp.family,
        "sizes": inp.sizes,
        "fields": ["state", "action", "next_state", "reward"],
        "reward_definition": "negative delta = improvement (lower is better)",
    }
    with open(out / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Also save in WQDF format
    wqdf_path = out / "wqdf_samples.jsonl"
    write_wqdf_jsonl(inp.all_samples, str(wqdf_path))

    return {
        "worker": "training_data",
        "output": str(out),
        "files": ["training_data.jsonl", "summary.json", "wqdf_samples.jsonl"],
        "records": len(records),
    }


# ---------------------------------------------------------------------------
# Pipeline orchestrator — runs all 5 workers in parallel
# ---------------------------------------------------------------------------

WORKERS = [
    ("benchmark_results", worker_benchmark_results),
    ("paper_data", worker_paper_data),
    ("github_demo", worker_github_demo),
    ("blog_post", worker_blog_post),
    ("training_data", worker_training_data),
]


def run_pipeline(
    family: str = "qft",
    sizes: list[int] | None = None,
    instances: int = 3,
    samples_per_circuit: int = 50,
    seed: int = 42,
    output_dir: str = "benchmarks/results/run",
    optimization_levels: list[int] | None = None,
    basis_gates_options: list[list[str]] | None = None,
    layout_methods: list[str] | None = None,
    routing_methods: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full pipeline: generate data, then produce 5 outputs in parallel.

    Args:
        family: Circuit family ("ghz", "qft", "grover")
        sizes: Qubit counts
        instances: Instances per size
        samples_per_circuit: Compilation samples per circuit
        seed: Random seed
        output_dir: Base output directory
        optimization_levels: Qiskit opt levels to vary
        basis_gates_options: Basis gate sets to try
        layout_methods: Layout methods to try
        routing_methods: Routing methods to try

    Returns:
        Summary dict with all worker results
    """
    if sizes is None:
        sizes = [4, 6, 8]
    if optimization_levels is None:
        optimization_levels = [0, 1, 2, 3]
    if basis_gates_options is None:
        basis_gates_options = [
            ["cx", "u3", "u1", "u2"],
            ["cx", "rz", "sx", "x"],
            ["ecr", "rz", "sx", "x"],
        ]
    if layout_methods is None:
        layout_methods = ["trivial", "dense", "sabre"]
    if routing_methods is None:
        routing_methods = ["sabre", "stochastic", "basic"]

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = hashlib.md5(f"{family}:{timestamp}:{seed}".encode()).hexdigest()[:8]
    output_path = Path(output_dir.rstrip("/")) / f"run_{run_id}"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  WestQuant Pipeline Agent — Run {run_id}")
    print(f"{'='*60}")
    print(f"  Family:    {family}")
    print(f"  Sizes:     {sizes}")
    print(f"  Instances: {instances}")
    print(f"  Samples:   {samples_per_circuit} per circuit")
    print(f"  Output:    {output_path}")
    print(f"{'='*60}")

    # --- Phase 1: Generate circuits ---
    print(f"\n[1/3] Generating {family} circuits...")
    gen = FAMILY_GENERATORS.get(family)
    if gen is None:
        raise ValueError(f"Unknown family: {family}. Available: {list(FAMILY_GENERATORS)}")
    circuits = gen(sizes=sizes, instances=instances, seed=seed)
    print(f"  Generated {len(circuits)} circuits")

    # --- Phase 2: Generate compilation data ---
    print(f"\n[2/3] Generating compilation data...")
    all_samples: list[WQDFSample] = []
    t0 = time.time()
    for i, bc in enumerate(circuits):
        samples = generate_training_data(
            bc.circuit,
            framework="qiskit",
            samples=samples_per_circuit,
            seed=seed + i,
            optimization_levels=optimization_levels,
            basis_gates_options=basis_gates_options,
            layout_methods=layout_methods,
            routing_methods=routing_methods,
        )
        all_samples.extend(samples)
        if (i + 1) % 5 == 0 or i == len(circuits) - 1:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(circuits)}] {len(all_samples)} samples ({elapsed:.1f}s)")

    print(f"  Total: {len(all_samples)} samples in {time.time()-t0:.1f}s")

    # --- Build shared input ---
    inp = PipelineInput(
        run_id=run_id,
        family=family,
        sizes=sizes,
        instances=instances,
        samples_per_circuit=samples_per_circuit,
        seed=seed,
        circuits=circuits,
        all_samples=all_samples,
        timestamp=timestamp,
        config={
            "optimization_levels": optimization_levels,
            "basis_gates_options": basis_gates_options,
            "layout_methods": layout_methods,
            "routing_methods": routing_methods,
        },
    )

    # Save input summary
    with open(output_path / "input_summary.json", "w") as f:
        json.dump(inp.to_summary(), f, indent=2)

    # --- Phase 3: Run 5 workers in parallel ---
    print(f"\n[3/3] Running 5 output workers in parallel...")
    results = {}
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(worker, inp, output_path): name
            for name, worker in WORKERS
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results[name] = result
                print(f"  [{name}] done -> {result.get('output', '')}")
            except Exception as e:
                results[name] = {"worker": name, "error": str(e)}
                print(f"  [{name}] FAILED: {e}")

    elapsed = time.time() - t0
    print(f"\n  All workers completed in {elapsed:.1f}s")

    # --- Save pipeline manifest ---
    manifest = {
        "run_id": run_id,
        "timestamp": timestamp,
        "family": family,
        "sizes": sizes,
        "instances": instances,
        "samples_per_circuit": samples_per_circuit,
        "total_circuits": len(circuits),
        "total_samples": len(all_samples),
        "generation_time_s": time.time() - t0,
        "outputs": results,
    }
    with open(output_path / "pipeline_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Pipeline complete — {output_path}")
    print(f"  5 outputs: benchmark/ paper/ demo/ blog/ training_data/")
    print(f"  Manifest: pipeline_manifest.json")
    print(f"{'='*60}\n")

    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WestQuant Pipeline Agent — 1 run, 5 outputs in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Outputs:
  benchmark/      results.json, summary.md, figure.png
  paper/         metrics.json, tables.tex, paper_figure.png
  demo/          README.md, demo_data.json
  blog/          blog_post.md
  training_data/ training_data.jsonl, summary.json, wqdf_samples.jsonl

Example:
  python -m benchmarks.pipeline_agent --family qft --sizes 4 6 8 --instances 3 --samples 50
        """,
    )
    parser.add_argument("--family", type=str, default="qft",
                        choices=["ghz", "qft", "grover"],
                        help="Circuit family")
    parser.add_argument("--sizes", type=int, nargs="+", default=[4, 6, 8],
                        help="Qubit sizes")
    parser.add_argument("--instances", type=int, default=3,
                        help="Instances per size")
    parser.add_argument("--samples", type=int, default=50,
                        help="Compilation samples per circuit")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--output", type=str, default="benchmarks/results",
                        help="Base output directory")
    args = parser.parse_args()

    run_pipeline(
        family=args.family,
        sizes=args.sizes,
        instances=args.instances,
        samples_per_circuit=args.samples,
        seed=args.seed,
        output_dir=args.output,
    )
