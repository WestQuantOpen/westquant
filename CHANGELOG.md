# Changelog

## 0.1.1

- Fix: `westquant compare` printed `verified=yes` for every Qiskit baseline and
  `Verification: EXACT` for the WestQuant result without running any check.
  Each row now shows the status returned by `QiskitEquivalenceVerifier`
  (`exact`, `invalid` or `unknown`), and reductions are only printed when the
  selected candidate is verified.
- `westquant compare -f pytket|pennylane|pulser` now exits with status 2 and a
  "not implemented" message instead of exiting 0.
- `-o 0` is no longer replaced by optimization level 2.
- `westquant version` / `doctor` report the installed package version instead
  of a hard-coded string.
- README: removed `from westquant import optimize` (never exported) and the
  synthetic compare output; documented the real search API and actual output.
- The `qiskit` and `all` extras now require `westquant-qiskit>=0.1.2`, whose
  stage plugins work on Qiskit 2.x.
- `westquant-qcsc` 0.2.0 no longer installs a `westquant` command, so this
  package is the only owner of `westquant`.
