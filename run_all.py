import time
import json
import sys
sys.path.insert(0, '.')

from src.generators.scenario_generator import generate_scenario
from src.algorithms.fifo import FIFOScheduler
from src.algorithms.greedy import PriorityGreedyScheduler
from src.evaluators.metrics import compute_metrics, compare_algorithms

# Instance size definitions matching Table in Section 4.1
SIZES = [
    ("XS", 10, 1, 10),
    ("S", 50, 2, 10),
    ("M", 100, 4, 10),
    ("L", 500, 8, 10),
    ("XL", 1000, 12, 10),
]

def run_one(num_satellites, num_requests, seed):
    satellites, requests = generate_scenario(num_satellites, num_requests, seed=seed)
    results = {}

    for name, sched_factory in [
        ("FIFO", lambda: FIFOScheduler),
        ("Greedy-P", lambda: PriorityGreedyScheduler),
        ("Greedy-PW", lambda: PriorityGreedyScheduler),
    ]:
        # Decentralized multi-satellite assignment: partition requests round-robin
        # across the constellation, then schedule each satellite independently.
        # (This was a gap in the original single-satellite appendix code — see
        # verification note: satellites beyond index 0 were previously unused.)
        buckets = [[] for _ in range(num_satellites)]
        for i, r in enumerate(requests):
            buckets[i % num_satellites].append(r)

        all_scheduled, all_rejected, all_reasons = [], [], []
        t0 = time.perf_counter()
        for s_idx in range(num_satellites):
            if name == "FIFO":
                sched = FIFOScheduler(sat_id=s_idx)
            elif name == "Greedy-P":
                sched = PriorityGreedyScheduler(by_window_length=False, sat_id=s_idx)
            else:
                sched = PriorityGreedyScheduler(by_window_length=True, sat_id=s_idx)
            sc, rj, rs = sched.schedule(buckets[s_idx], satellites)
            all_scheduled += sc
            all_rejected += rj
            all_reasons += rs
        runtime_ms = (time.perf_counter() - t0) * 1000

        # energy/storage % is reported per-satellite average
        results[name] = compute_metrics(all_scheduled, all_rejected, runtime_ms, all_reasons, satellites[0])

    comparison = compare_algorithms(results)
    return results, comparison


def main():
    all_results = {}
    for name, n_tasks, n_sats, n_instances in SIZES:
        print(f"=== {name}: {n_tasks} tasks, {n_sats} satellites, {n_instances} instances ===")
        size_results = []
        for inst in range(n_instances):
            seed = hash((name, inst)) % (2**31)
            results, comparison = run_one(n_sats, n_tasks, seed)
            size_results.append({"results": results, "comparison": comparison})
        all_results[name] = size_results

        # Print quick summary
        for alg in ["FIFO", "Greedy-P", "Greedy-PW"]:
            avg_priority = sum(r["results"][alg]["total_priority"] for r in size_results) / n_instances
            avg_runtime = sum(r["results"][alg]["runtime_ms"] for r in size_results) / n_instances
            avg_completion = sum(r["results"][alg]["completion_rate"] for r in size_results) / n_instances
            print(f"  {alg}: avg_priority={avg_priority:.1f}, avg_runtime={avg_runtime:.3f}ms, "
                  f"avg_completion={avg_completion:.3f}")

    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nSaved to results.json")


if __name__ == "__main__":
    main()
