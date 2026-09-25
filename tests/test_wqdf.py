"""Tests for WQDF dataset format and ML data generation."""
import json
import os
import tempfile

import pytest

from westquant.wqdf import (
    WQDFSample,
    WQDF_VERSION,
    write_wqdf_jsonl,
    read_wqdf_jsonl,
    wqdf_schema,
)
from westquant.generate import generate_training_data


def test_wqdf_version():
    assert WQDF_VERSION == "wqdf-v0.1"


def test_wqdf_sample_creation():
    sample = WQDFSample(
        problem="maxcut",
        algorithm="qaoa_p1",
        circuit="OPENQASM 2.0;",
        representation="qiskit:sabre:opt3",
        backend="aer",
        num_qubits=4,
        depth=10,
        two_qubit_gates=6,
        size=20,
        swap_gates=2,
        sample_id="wqdf-qiskit-000001",
        framework="qiskit",
    )
    assert sample.problem == "maxcut"
    assert sample.algorithm == "qaoa_p1"
    assert sample.num_qubits == 4
    assert sample.depth == 10
    assert sample.two_qubit_gates == 6
    assert sample.schema_version == WQDF_VERSION


def test_wqdf_sample_defaults():
    sample = WQDFSample()
    assert sample.problem == ""
    assert sample.algorithm == ""
    assert sample.num_qubits == 0
    assert sample.depth == 0
    assert sample.energy is None
    assert sample.fidelity is None
    assert sample.optimization_trajectory == []
    assert sample.schema_version == WQDF_VERSION


def test_wqdf_sample_to_dict():
    sample = WQDFSample(
        problem="vqe",
        algorithm="vqe_twolocal",
        num_qubits=2,
        depth=5,
        sample_id="test-001",
        framework="qiskit",
    )
    d = sample.to_dict()
    assert d["problem"] == "vqe"
    assert d["num_qubits"] == 2
    assert d["schema_version"] == WQDF_VERSION
    assert isinstance(d, dict)


def test_wqdf_sample_to_json():
    sample = WQDFSample(
        problem="maxcut",
        num_qubits=3,
        sample_id="test-002",
    )
    j = sample.to_json()
    d = json.loads(j)
    assert d["problem"] == "maxcut"
    assert d["num_qubits"] == 3
    assert d["sample_id"] == "test-002"
    assert d["schema_version"] == WQDF_VERSION


def test_wqdf_sample_from_dict():
    d = {
        "problem": "qaoa",
        "algorithm": "qaoa_p2",
        "num_qubits": 6,
        "depth": 15,
        "sample_id": "test-003",
        "framework": "qiskit",
        "schema_version": "wqdf-v0.1",
        "extra_field": "ignored",
    }
    sample = WQDFSample.from_dict(d)
    assert sample.problem == "qaoa"
    assert sample.algorithm == "qaoa_p2"
    assert sample.num_qubits == 6
    assert sample.depth == 15
    assert sample.schema_version == WQDF_VERSION


def test_wqdf_sample_from_dict_ignores_unknown():
    d = {
        "problem": "vqe",
        "unknown_field": "should be ignored",
    }
    sample = WQDFSample.from_dict(d)
    assert sample.problem == "vqe"


def test_write_read_jsonl_roundtrip():
    samples = [
        WQDFSample(
            problem="maxcut",
            algorithm="qaoa_p1",
            num_qubits=4,
            depth=10,
            two_qubit_gates=6,
            sample_id="wqdf-qiskit-000000",
            framework="qiskit",
        ),
        WQDFSample(
            problem="vqe",
            algorithm="vqe_twolocal",
            num_qubits=2,
            depth=5,
            two_qubit_gates=3,
            sample_id="wqdf-qiskit-000001",
            framework="qiskit",
        ),
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name

    try:
        count = write_wqdf_jsonl(samples, path)
        assert count == 2

        loaded = read_wqdf_jsonl(path)
        assert len(loaded) == 2

        assert loaded[0].problem == "maxcut"
        assert loaded[0].num_qubits == 4
        assert loaded[0].depth == 10
        assert loaded[0].two_qubit_gates == 6
        assert loaded[0].sample_id == "wqdf-qiskit-000000"
        assert loaded[0].schema_version == WQDF_VERSION

        assert loaded[1].problem == "vqe"
        assert loaded[1].num_qubits == 2
        assert loaded[1].sample_id == "wqdf-qiskit-000001"
    finally:
        os.unlink(path)


def test_read_jsonl_empty_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"problem": "maxcut", "num_qubits": 2}\n')
        f.write("\n")
        f.write('{"problem": "vqe", "num_qubits": 3}\n')
        path = f.name

    try:
        loaded = read_wqdf_jsonl(path)
        assert len(loaded) == 2
        assert loaded[0].problem == "maxcut"
        assert loaded[1].problem == "vqe"
    finally:
        os.unlink(path)


def test_wqdf_schema():
    schema = wqdf_schema()
    assert schema["schema_version"] == WQDF_VERSION
    assert "fields" in schema
    assert "problem" in schema["fields"]
    assert "num_qubits" in schema["fields"]
    assert "depth" in schema["fields"]
    assert "circuit" in schema["fields"]
    assert "backend" in schema["fields"]
    assert "framework" in schema["fields"]
    assert "sample_id" in schema["fields"]


def test_generate_training_data_with_mock():
    """Test generate_training_data with a mock circuit object."""
    class MockCircuit:
        num_qubits = 3
        name = "qaoa_maxcut"
        
        def qasm(self):
            return "OPENQASM 2.0; include 'qelib1.inc'; qreg q[3];"
    
    circuit = MockCircuit()
    dataset = generate_training_data(
        circuit,
        framework="qiskit",
        backend="aer",
        samples=10,
        output_format="jsonl",
    )
    
    assert len(dataset) > 0
    assert len(dataset) <= 10
    
    for sample in dataset:
        assert isinstance(sample, WQDFSample)
        assert sample.schema_version == WQDF_VERSION
        assert sample.framework == "qiskit"
        assert sample.backend == "aer"
        assert sample.num_qubits == 3
        assert sample.sample_id.startswith("wqdf-qiskit-")
        assert sample.problem == "combinatorial_optimization"


def test_generate_training_data_writes_jsonl():
    """Test that generate_training_data writes a JSONL file."""
    class MockCircuit:
        num_qubits = 2
        name = "vqe_twolocal"
        
        def qasm(self):
            return "OPENQASM 2.0;"
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name

    try:
        dataset = generate_training_data(
            MockCircuit(),
            framework="qiskit",
            backend="aer",
            samples=5,
            output_format="jsonl",
            output_path=path,
        )
        
        assert len(dataset) > 0
        assert os.path.exists(path)
        
        loaded = read_wqdf_jsonl(path)
        assert len(loaded) == len(dataset)
        assert loaded[0].framework == "qiskit"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_generate_training_data_with_qiskit():
    """Test generate_training_data with a real Qiskit circuit if available."""
    try:
        from qiskit import QuantumCircuit
    except ImportError:
        pytest.skip("qiskit not installed")

    qc = QuantumCircuit(3, name="qaoa_maxcut")
    qc.h([0, 1, 2])
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(0, 2)

    dataset = generate_training_data(
        qc,
        framework="qiskit",
        backend="aer",
        samples=5,
        output_format="jsonl",
    )

    assert len(dataset) > 0
    for sample in dataset:
        assert isinstance(sample, WQDFSample)
        assert sample.framework == "qiskit"
        assert sample.num_qubits == 3
