# LinkedIn Post 2: Representation Search Beats Fixed Optimization Levels

**Image:** linkedin_2_representation_search.png

---

Qiskit gives you 4 optimization levels. We searched 200+ compilation configurations and found better circuits.

Same QFT algorithm. Same hardware target. Different representation.

The difference:
- Qiskit opt=3 (fixed): baseline 2Q gate count
- WestQuant search: up to 33% fewer 2-qubit gates

On real hardware, fewer 2-qubit gates = lower error = higher fidelity. This isn't marginal — it's the difference between a circuit that works and one that doesn't on noisy intermediate-scale quantum devices.

Why does this work?

The order and combination of transpiler passes significantly affects the final circuit. Qiskit's StagedPassManager exists precisely because this matters. But most users never explore beyond the default level.

WestQuant Open searches this space systematically:
- 4 optimization levels × 3 basis gate sets × 3 layout methods × 3 routing methods
- Each combination is a different representation
- The best one wins

And every search produces training data. Each compilation path becomes a (state, action, next_state, reward) tuple — the raw material for WQT20, which will learn to predict the best policy without searching.

The pipeline runs in parallel: one benchmark produces benchmark results, paper data, a GitHub demo, a blog post, and WQT20 training data — all at once.

pip install westquant[qiskit]

github.com/WestQuantOpen

#QuantumComputing #Qiskit #QuantumCompilation #RepresentationSearch #OpenSource #QuantumSoftware #WestQuantOpen
