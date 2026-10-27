"""WQBench v0.1: explicit targets, provenance, conservative verification, resumable runs.

No hardware submission. No noise simulation. Synthetic error-product is a proxy.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import time

SCHEMA='wqbench-0.1'

def encoded(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)

def digest(obj):
    return hashlib.sha256(encoded(obj).encode()).hexdigest()

def circuit_document(qc):
    """Exact indexed instruction identity, NOT semantic canonicalization."""
    if qc.parameters: raise ValueError('Bind all parameters before collecting labels')
    return {'schema':SCHEMA,'qubits':qc.num_qubits,'clbits':qc.num_clbits,
        'global_phase':float(qc.global_phase).hex(),
        'instructions':[{'name':i.operation.name,'q':[qc.find_bit(q).index for q in i.qubits],
            'c':[qc.find_bit(c).index for c in i.clbits],
            'params':[float(p).hex() for p in i.operation.params]} for i in qc.data]}

def split_for_root(root_id,seed=20261027):
    if not isinstance(root_id,str) or not root_id.strip(): raise ValueError('Explicit nonempty root_id required')
    value=int(digest(['root-split-v1',seed,root_id])[:16],16)/(1<<64)
    return 'train' if value<.8 else ('validation' if value<.9 else 'test')

@dataclass(frozen=True)
class TargetSpec:
    name: str
    num_qubits: int
    topology: str='line'
    one_qubit_error: float=.001
    two_qubit_error: float=.01
    readout_error: float=.02
    one_qubit_seconds: float=20e-9
    two_qubit_seconds: float=200e-9
    measurement_seconds: float=800e-9
    provenance: str='synthetic'
    source: str='WQBench illustrative profile; not a device calibration'

    def build(self):
        from qiskit.circuit import Parameter
        from qiskit.circuit.library import RZGate,SXGate,XGate,CXGate
        from qiskit.circuit import Measure
        from qiskit.transpiler import Target,InstructionProperties
        if self.provenance!='synthetic': raise ValueError('Measured profiles require a separate calibrated adapter')
        if self.num_qubits<2 or self.num_qubits>30: raise ValueError('Target width must be 2–30')
        if self.topology not in ('line','ring','all_to_all'):raise ValueError('Unsupported topology')
        for x in (self.one_qubit_error,self.two_qubit_error,self.readout_error):
            if not math.isfinite(x) or not 0<=x<=1:raise ValueError('Invalid error probability')
        for x in (self.one_qubit_seconds,self.two_qubit_seconds,self.measurement_seconds):
            if not math.isfinite(x) or x<0: raise ValueError('Invalid duration in seconds')
        n=self.num_qubits
        if self.topology=='all_to_all': edges={(i,j) for i in range(n) for j in range(n) if i!=j}
        else:
            pairs={(i,i+1) for i in range(n-1)}
            if self.topology=='ring':pairs.add((0,n-1))
            edges={e for i,j in pairs for e in ((i,j),(j,i))}
        t=Target(num_qubits=n)
        for gate,duration,error in [(RZGate(Parameter('angle')),0,0),(SXGate(),self.one_qubit_seconds,self.one_qubit_error),(XGate(),self.one_qubit_seconds,self.one_qubit_error),(Measure(),self.measurement_seconds,self.readout_error)]:
            t.add_instruction(gate,{(q,):InstructionProperties(duration=duration,error=error) for q in range(n)})
        t.add_instruction(CXGate(),{e:InstructionProperties(duration=self.two_qubit_seconds,error=self.two_qubit_error) for e in sorted(edges)})
        return t


def raw_metrics(qc,target=None):
    counts=dict(qc.count_ops());duration=0.;proxy=1.;known=target is not None
    for i in qc.data:
        if i.operation.name=='barrier':continue
        if target is not None:
            qs=tuple(qc.find_bit(q).index for q in i.qubits)
            try:p=target[i.operation.name][qs]
            except KeyError:known=False;continue
            if p is None or p.duration is None or p.error is None:known=False;continue
            duration+=p.duration;proxy*=1-p.error
    return {'depth':qc.depth(),'size':qc.size(),'two_qubit_gates':sum(len(i.qubits)==2 for i in qc.data if i.operation.name!='barrier'),
        'operation_counts':counts,'gate_time_sum_seconds':duration if known else None,
        'independent_gate_success_proxy':proxy if known else None,
        'metric_provenance':'structural; target-derived independent-product proxy, not physical fidelity'}


def target_valid(qc,target):
    return all(i.operation.name=='barrier' or target.instruction_supported(operation_name=i.operation.name,qargs=tuple(qc.find_bit(q).index for q in i.qubits)) for i in qc.data)


def verify(source,compiled,max_qubits=8):
    from qiskit.quantum_info import Operator
    if max(source.num_qubits,compiled.num_qubits)>max_qubits:
        return {'status':'UNKNOWN','reason':'exact_operator_width_limit','max_qubits':max_qubits}
    if source.num_qubits!=compiled.num_qubits:
        return {'status':'UNKNOWN','reason':'ancilla_isometry_not_implemented'}
    if any(i.operation.name in ('measure','reset','if_else','while_loop','for_loop') for q in (source,compiled) for i in q.data):
        return {'status':'UNKNOWN','reason':'nonunitary_or_measurement_mapping_not_verified'}
    a=source;b=compiled
    if any(i.operation.name in ('measure','reset','if_else','while_loop','for_loop') for q in (a,b) for i in q.data):
        return {'status':'UNKNOWN','reason':'nonunitary_or_control_flow'}
    try:
        # Operator.from_circuit includes initial/final layout permutations.
        left=Operator.from_circuit(a);right=Operator.from_circuit(b)
        same=bool(left.equiv(right,atol=1e-9,rtol=1e-9))
        return {'status':'EXACT' if same else 'FAILED','method':'full_layout_corrected_operator_up_to_global_phase','atol':1e-9,'rtol':1e-9}
    except Exception as e:return {'status':'UNKNOWN','reason':str(e)}


def normalized_regret(selected,baseline,oracle,tolerance=1e-12):
    """Conditional improvement-normalized cost regret; no opportunity => undefined."""
    if not all(math.isfinite(x) for x in (selected,baseline,oracle)):raise ValueError('Finite costs required')
    if selected<oracle-tolerance:raise ValueError('Selected cost beats declared oracle; inconsistent pool')
    gain=baseline-oracle
    if gain<=tolerance:return None
    return (selected-oracle)/gain


class Engine:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        for table,key in [('circuits','circuit_id'),('backends','backend_id'),('runs','run_id')]:
            self.db.execute(f'CREATE TABLE IF NOT EXISTS {table} ({key} TEXT PRIMARY KEY, document TEXT NOT NULL)')
        self.db.commit()
        self.environment={'qiskit':importlib.metadata.version('qiskit'),'engine_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        try:self.environment['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).parent,text=True,stderr=subprocess.DEVNULL).strip()
        except Exception:self.environment['git_commit']=None
        try:self.environment['git_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=Path(__file__).parent,text=True,stderr=subprocess.DEVNULL).strip())
        except Exception:self.environment['git_dirty']=None

    def __enter__(self):return self
    def __exit__(self,*args):self.db.close()

    def put(self,table,key,value):
        self.db.execute(f'INSERT INTO {table} VALUES (?,?)',(key,encoded(value)));self.db.commit()

    def compile(self,qc,*,root_id,family,target_spec,optimization_level=1,seed=0):
        from qiskit import transpile,qasm3
        if optimization_level not in (0,1,2,3):raise ValueError('Optimization level must be 0–3')
        split=split_for_root(root_id)
        circuit_id=digest(circuit_document(qc));spec=asdict(target_spec);target=target_spec.build();backend_id=digest(spec)
        row=self.db.execute('SELECT document FROM circuits WHERE circuit_id=?',(circuit_id,)).fetchone()
        if row:
            if json.loads(row[0])['root_id']!=root_id:raise ValueError('Duplicate circuit registered under different roots; merge lineage before benchmark')
        else:self.put('circuits',circuit_id,{'circuit_id':circuit_id,'root_id':root_id,'family':family,'split':split,'qasm3':qasm3.dumps(qc),'instruction_document':circuit_document(qc),'metrics':raw_metrics(qc)})
        if not self.db.execute('SELECT 1 FROM backends WHERE backend_id=?',(backend_id,)).fetchone():self.put('backends',backend_id,{'backend_id':backend_id,**spec})
        config={'optimization_level':optimization_level,'seed_transpiler':seed,'verification_max_qubits':8}
        run_id=digest({'schema':SCHEMA,'circuit_id':circuit_id,'backend_id':backend_id,'config':config,'environment':self.environment})
        prior=self.db.execute('SELECT document FROM runs WHERE run_id=?',(run_id,)).fetchone()
        if prior:return json.loads(prior[0]),True
        record={'schema':SCHEMA,'run_id':run_id,'circuit_id':circuit_id,'backend_id':backend_id,'root_id':root_id,'split':split,'config':config,'environment':self.environment,
            'status':None,'error':None,'target_valid':None,'verification':{'status':'UNKNOWN','reason':'compilation_not_completed'},'before':raw_metrics(qc),'after':None,'compiled_qasm3':None}
        started=time.perf_counter()
        try:
            compiled=transpile(qc,target=target,optimization_level=optimization_level,seed_transpiler=seed)
            record['target_valid']=target_valid(compiled,target)
            record['verification']=verify(qc,compiled)
            record['after']=raw_metrics(compiled,target);record['compiled_qasm3']=qasm3.dumps(compiled)
            record['status']='invalid_target' if not record['target_valid'] else ('verification_failed' if record['verification']['status']=='FAILED' else 'success')
        except Exception as e:record['status']='compile_error';record['error']={'type':type(e).__name__,'message':str(e)}
        record['compile_and_verify_seconds']=time.perf_counter()-started
        record['eligible_for_exact_training']=record['status']=='success' and record['verification']['status']=='EXACT'
        self.put('runs',run_id,record)
        return record,False

    def export(self,directory):
        p=Path(directory);p.mkdir(parents=True,exist_ok=True)
        counts={}
        for table in ('circuits','backends','runs'):
            key={'circuits':'circuit_id','backends':'backend_id','runs':'run_id'}[table]
            rows=list(self.db.execute(f'SELECT document FROM {table} ORDER BY {key}'))
            (p/f'{table}.jsonl').write_text(''.join(row[0]+'\n' for row in rows),encoding='utf-8');counts[table]=len(rows)
        return counts


def workload():
    import random
    from qiskit import QuantumCircuit
    for family in ('ghz','qaoa','random'):
        for n in (3,4):
            for seed in (11,29):
                rng=random.Random(seed);q=QuantumCircuit(n)
                if family=='ghz':
                    q.h(0)
                    for i in range(1,n):q.cx(0,i)
                    # Distinct angle instances; all descendants keep this root.
                    q.rz(rng.uniform(-1,1),n-1)
                elif family=='qaoa':
                    q.h(range(n))
                    for i in range(n-1):q.rzz(rng.uniform(-1,1),i,i+1)
                    q.rx(.3,range(n))
                else:
                    for _ in range(3*n):
                        i=rng.randrange(n);q.ry(rng.uniform(-math.pi,math.pi),i);q.cx(i,(i+1)%n)
                root=f'{family}:{n}' if family=='ghz' else f'{family}:{n}:{seed}'
                yield root,family,q


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default='wqbench.sqlite');parser.add_argument('--export',default='wqbench_export');parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();cases=list(workload());count=len(cases)*2*4*2
    if args.dry_run:print(encoded({'circuits':len(cases),'compilations':count,'hardware_jobs':0}));return
    created=cached=0
    with Engine(args.db) as engine:
        for root,family,q in cases:
            for topology in ('line','ring'):
                for level in range(4):
                    for seed in (101,202):
                        _,hit=engine.compile(q,root_id=root,family=family,target_spec=TargetSpec(f'{topology}-{q.num_qubits}',q.num_qubits,topology),optimization_level=level,seed=seed)
                        cached+=int(hit);created+=int(not hit)
        exported=engine.export(args.export)
    print(encoded({'created':created,'cache_hits':cached,'exported':exported,'planned_compilations':count}))

if __name__=='__main__':main()
