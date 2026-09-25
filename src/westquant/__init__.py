"""WestQuant Open — Search the representation, not just the parameters.

Umbrella package for the WestQuant Open ecosystem. Install with:

    pip install westquant[qiskit]
    pip install westquant[all]

Then run:

    westquant doctor     # Check what's installed and working
    westquant compare     # Compare default vs WestQuant search
"""
__version__ = "0.1.0a2"

from .wqdf import WQDFSample, WQDF_VERSION, write_wqdf_jsonl, read_wqdf_jsonl, wqdf_schema
from .generate import generate_training_data
