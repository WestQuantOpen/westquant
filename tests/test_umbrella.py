"""Tests for the WestQuant umbrella package."""
import pytest


def test_import():
    import westquant
    assert westquant.__version__ == "0.1.1"


def test_cli_import():
    from westquant.cli import main
    assert callable(main)


def test_doctor_runs():
    from westquant.cli import cmd_doctor
    import argparse
    args = argparse.Namespace()
    result = cmd_doctor(args)
    assert result == 0


def test_plugins_runs():
    from westquant.cli import cmd_plugins
    import argparse
    args = argparse.Namespace()
    result = cmd_plugins(args)
    assert result == 0


def test_version_runs():
    from westquant.cli import cmd_version
    import argparse
    args = argparse.Namespace()
    result = cmd_version(args)
    assert result == 0


def _compare(tmp_path, capsys, circuit, framework="qiskit"):
    import argparse
    from qiskit import qasm2
    from westquant.cli import cmd_compare

    path = tmp_path / "c.qasm"
    qasm2.dump(circuit, str(path))
    code = cmd_compare(argparse.Namespace(circuit=str(path), framework=framework, optimization_level=2))
    return code, capsys.readouterr()


def _bell(measure=False):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    if measure:
        qc.measure_all()
    return qc


def test_compare_reports_exact_only_from_verifier(tmp_path, capsys):
    pytest.importorskip("westquant_qiskit")
    code, out = _compare(tmp_path, capsys, _bell())
    assert code == 0
    assert "Verification of selected candidate: exact" in out.out
    assert " yes" not in out.out


def test_compare_never_claims_exact_for_unverifiable_circuit(tmp_path, capsys):
    pytest.importorskip("westquant_qiskit")
    code, out = _compare(tmp_path, capsys, _bell(measure=True))
    assert code == 0
    assert "exact" not in out.out.lower().replace("verified exact", "")
    assert "Verification of selected candidate: unknown" in out.out
    assert "reductions are not reported" in out.out


@pytest.mark.parametrize("framework", ["pytket", "pennylane", "pulser"])
def test_compare_unimplemented_frameworks_fail(tmp_path, capsys, framework):
    pytest.importorskip("qiskit")
    code, out = _compare(tmp_path, capsys, _bell(), framework)
    assert code == 2
    assert "not implemented" in out.err


def test_readme_only_documents_exported_api():
    from pathlib import Path
    import re
    import westquant

    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    for name in re.findall(r"from westquant import ([\w, ]+)", readme):
        for symbol in name.split(","):
            assert hasattr(westquant, symbol.strip()), symbol
