"""
explore_schedule.py

Run ONE test scenario with your own choice of satellites and tasks, see the
actual schedule produced by each algorithm, and save a visual timeline.

Usage:
    python explore_schedule.py
    python explore_schedule.py --satellites 3 --tasks 30 --seed 7

Outputs:
    - A printed comparison summary (priority, completion rate, runtime)
    - A printed, human-readable schedule (which request, which satellite,
      what time) for whichever algorithm you pick with --show
    - A Gantt-style timeline image: schedule_timeline.png
"""
import argparse
import sys
sys.path.insert(0, '.')

from src.generators.scenario_generator import generate_scenario
from src.algorithms.fifo import FIFOScheduler
from src.algorithms.greedy import PriorityGreedyScheduler
from src.evaluators.metrics import compute_metrics

import matplotlib
matplotlib.use("Agg")  # no display needed, just save to file
import matplotlib.pyplot as plt


def run_all_algorithms(satellites, requests, n_satellites):
    """Partition requests round-robin across satellites and run each
    algorithm independently on each satellite (decentralized scheduling,
    matching the paper's Section 4.1 correction)."""
    buckets = [[] for _ in range(n_satellites)]
    for i, r in enumerate(requests):
        buckets[i % n_satellites].append(r)

    algorithms = {
        "FIFO": lambda sid: FIFOScheduler(sat_id=sid),
        "Greedy-P": lambda sid: PriorityGreedyScheduler(by_window_length=False, sat_id=sid),
        "Greedy-PW": lambda sid: PriorityGreedyScheduler(by_window_length=True, sat_id=sid),
    }

    all_results = {}
    schedules = {}  # per algorithm: list of (satellite_id, request, start, end)

    for name, factory in algorithms.items():
        scheduled_all, rejected_all, reasons_all = [], [], []
        timeline = []
        for s_idx in range(n_satellites):
            sched = factory(s_idx)
            sc, rj, rs = sched.schedule(buckets[s_idx], satellites)
            scheduled_all += sc
            rejected_all += rj
            reasons_all += rs
            # Recompute timing for display purposes
            sat = satellites[s_idx]
            current_time, current_angle = 0.0, 0.0
            for req in (sc if name == "FIFO" else
                        sorted(sc, key=lambda x: (-x.priority, x.window_length if name == "Greedy-PW" else x.earliest_start))):
                slew = sat.slew_time(current_angle, req.roll_angle)
                start = max(current_time + slew, req.earliest_start)
                end = start + req.duration
                timeline.append((s_idx, req, start, end))
                current_time, current_angle = end, req.roll_angle
        all_results[name] = compute_metrics(scheduled_all, rejected_all, 0.0, reasons_all, satellites[0])
        schedules[name] = timeline

    return all_results, schedules


def print_summary(results):
    print(f"\n{'Algorithm':<12}{'Priority':>10}{'Scheduled':>11}{'Rejected':>10}{'Completion':>12}")
    print("-" * 55)
    for name, m in results.items():
        print(f"{name:<12}{m['total_priority']:>10.0f}{m['scheduled_count']:>11}"
              f"{m['rejected_count']:>10}{m['completion_rate']*100:>11.1f}%")


def print_schedule(timeline, alg_name, max_rows=25):
    print(f"\n--- Schedule detail: {alg_name} (first {max_rows} entries, sorted by start time) ---")
    print(f"{'Satellite':<10}{'Request':<10}{'Priority':>9}{'Start (s)':>11}{'End (s)':>10}")
    for s_idx, req, start, end in sorted(timeline, key=lambda x: x[2])[:max_rows]:
        print(f"S{s_idx+1:<9}{req.id:<10}{req.priority:>9}{start:>11.1f}{end:>10.1f}")
    if len(timeline) > max_rows:
        print(f"... and {len(timeline) - max_rows} more (full list not truncated in the saved plot)")


def plot_timeline(timeline, n_satellites, out_path="schedule_timeline.png"):
    fig, ax = plt.subplots(figsize=(11, 1.2 + 0.6 * n_satellites))
    colors = plt.cm.viridis_r
    max_priority = 10
    for s_idx, req, start, end in timeline:
        ax.barh(s_idx, end - start, left=start, height=0.6,
                color=colors(req.priority / max_priority), edgecolor="black", linewidth=0.3)
    ax.set_yticks(range(n_satellites))
    ax.set_yticklabels([f"Satellite {i+1}" for i in range(n_satellites)])
    ax.set_xlabel("Time (seconds)")
    ax.set_title("Schedule timeline (color = request priority, darker = higher)")
    sm = plt.cm.ScalarMappable(cmap=colors, norm=plt.Normalize(1, max_priority))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Priority", shrink=0.7)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"\nSaved timeline image to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Explore a single scheduling scenario.")
    parser.add_argument("--satellites", type=int, default=2, help="Number of satellites")
    parser.add_argument("--tasks", type=int, default=25, help="Number of observation requests")
    parser.add_argument("--seed", type=int, default=1, help="Random seed (change for a different scenario)")
    parser.add_argument("--show", type=str, default="Greedy-P",
                         choices=["FIFO", "Greedy-P", "Greedy-PW"],
                         help="Which algorithm's schedule to print and plot in detail")
    parser.add_argument("--output", type=str, default=None,
                         help="Output image filename. Defaults to a name that encodes the "
                              "scenario parameters (e.g. schedule_s2_t25_seed1_Greedy-P.png) "
                              "so successive runs don't overwrite each other.")
    args = parser.parse_args()

    print(f"Generating scenario: {args.satellites} satellite(s), {args.tasks} task(s), seed={args.seed}")
    satellites, requests = generate_scenario(args.satellites, args.tasks, seed=args.seed)

    results, schedules = run_all_algorithms(satellites, requests, args.satellites)

    print_summary(results)
    print_schedule(schedules[args.show], args.show)

    out_path = args.output or f"schedule_s{args.satellites}_t{args.tasks}_seed{args.seed}_{args.show}.png"
    plot_timeline(schedules[args.show], args.satellites, out_path=out_path)


if __name__ == "__main__":
    main()
