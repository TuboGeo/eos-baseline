# EOS Baseline Scheduling Framework

A reproducible, open-source baseline framework for benchmarking Earth Observation
constellation schedulers. Implements FIFO and priority-based greedy heuristics,
with an optional MILP-optimal reference solver for small instances.

Companion code for: *A Reproducible Baseline Framework for Benchmarking Earth
Observation Constellation Schedulers* (Warekuromor).

## Requirements

- Python 3.10 or later
- pip

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running the experiment suite

```
python run_all.py
```

This generates 10 synthetic instances at each of five scales (XS: 10 tasks,
S: 50, M: 100, L: 500, XL: 1000), schedules each with FIFO, Greedy-P, and
Greedy-PW, and writes summary metrics to the console and to `results.json`.

## Project structure

```
eos_baseline/
├── run_all.py                     # main experiment runner
├── requirements.txt
├── src/
│   ├── core/
│   │   ├── satellite.py           # satellite kinematics and resource model
│   │   └── request.py             # observation request model
│   ├── algorithms/
│   │   ├── base.py                # Scheduler interface
│   │   ├── fifo.py                # FIFO baseline
│   │   ├── greedy.py              # Greedy-P / Greedy-PW
│   │   └── milp.py                # OR-Tools CP-SAT optimal reference
│   ├── generators/
│   │   └── scenario_generator.py  # synthetic instance generator
│   └── evaluators/
│       └── metrics.py             # scoring and comparison utilities
```

## Adding a new algorithm

Implement the `Scheduler` interface in `src/algorithms/base.py`:

```python
from src.algorithms.base import Scheduler

class MyScheduler(Scheduler):
    def schedule(self, requests, satellites):
        scheduled, rejected, reasons = [], [], []
        # ... your logic here ...
        return scheduled, rejected, reasons
```

Then plug it into `run_all.py` alongside FIFO and Greedy-P.

## Known limitations (see paper Section 5.2)

- Multi-satellite assignment is a simple round-robin partition, not a jointly
  optimized assignment.
- Access windows are single-pass (no multi-orbit-pass propagation).
- Scenario parameters are drawn from published ranges typical of agile EO
  satellites in general, not from a specific NASRDA spacecraft, since one is
  not yet operational. Recalibrate `src/generators/scenario_generator.py`
  once real spacecraft parameters are available.

## License

MIT — see `LICENSE`.
