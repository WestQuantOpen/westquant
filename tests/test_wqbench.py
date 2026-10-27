import json
from dataclasses import replace
import pytest
qiskit=pytest.importorskip('qiskit')
from qiskit import QuantumCircuit,transpile
from westquant.wqbench import Engine,TargetSpec,digest,circuit_document,split_for_root,verify,normalized_regret,target_valid

def example():
    q=QuantumCircuit(3);q.h(0);q.cx(0,2);q.ry(.17,1);return q

def test_real_routing_and_layout():
    q=example();t=TargetSpec('line',3).build()
    c=transpile(q,target=t,optimization_level=3,seed_transpiler=12,initial_layout=[2,0,1])
    assert target_valid(c,t)
    assert verify(q,c)['status']=='EXACT'
    bad=q.copy();bad.x(0)
    assert verify(q,bad)['status']=='FAILED'

def test_unknown_no_fake_verification():
    q=QuantumCircuit(9)
    assert verify(q,q)['status']=='UNKNOWN'
    m=QuantumCircuit(2,2);m.measure([0,1],[0,1])
    assert verify(m,m)['status']=='UNKNOWN'

def test_identity_and_lineage():
    q=example();other=q.copy();other.x(1)
    assert digest(circuit_document(q))!=digest(circuit_document(other))
    q.name='different_label'
    assert digest(circuit_document(q))==digest(circuit_document(example()))
    assert split_for_root('root')==split_for_root('root')
    with pytest.raises(ValueError):split_for_root('')

def test_target_changes_measurements_and_cache(tmp_path):
    t=TargetSpec('profile',3);q=example()
    with Engine(tmp_path/'runs.sqlite') as e:
        r,hit=e.compile(q,root_id='a',family='test',target_spec=t)
        assert not hit and r['eligible_for_exact_training']
        same,hit=e.compile(q,root_id='a',family='test',target_spec=t)
        assert hit and same['run_id']==r['run_id']
        changed,hit=e.compile(q,root_id='a',family='test',target_spec=replace(t,two_qubit_error=.2))
        assert not hit and changed['run_id']!=r['run_id']
        assert changed['after']['independent_gate_success_proxy']<r['after']['independent_gate_success_proxy']
        assert r['before']['gate_time_sum_seconds'] is None
        with pytest.raises(ValueError,match='different roots'):e.compile(q,root_id='b',family='test',target_spec=t)
        assert e.export(tmp_path/'export')=={'circuits':1,'backends':2,'runs':2}

def test_failure_not_zero_metrics(tmp_path):
    with Engine(tmp_path/'x.sqlite') as e:
        r,hit=e.compile(example(),root_id='a',family='test',target_spec=TargetSpec('too_small',2))
        assert not hit and r['status']=='compile_error'
        assert r['after'] is None and r['error'] and not r['eligible_for_exact_training']

def test_regret_without_opportunity():
    assert normalized_regret(10,10,10) is None
    assert normalized_regret(9,10,8)==.5
    with pytest.raises(ValueError):normalized_regret(7,10,8)

def test_invalid_profile_rejected():
    with pytest.raises(ValueError):TargetSpec('bad',3,two_qubit_error=-1).build()
    with pytest.raises(ValueError):TargetSpec('unverified_measured',3,provenance='measured').build()


def test_parameter_descendants_share_split(tmp_path):
    with Engine(tmp_path/'lineage.sqlite') as e:
        a=example();b=example();b.rz(.291,1)
        first,_=e.compile(a,root_id='one-parent',family='derived',target_spec=TargetSpec('line',3))
        second,_=e.compile(b,root_id='one-parent',family='derived',target_spec=TargetSpec('line',3))
        assert first['circuit_id']!=second['circuit_id']
        assert first['root_id']==second['root_id'] and first['split']==second['split']
