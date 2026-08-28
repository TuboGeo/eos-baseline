"""
app.py — local browser interface for the EOS baseline scheduling framework.

Run with:
    streamlit run app.py

Opens a browser tab at http://localhost:8501 (nothing is exposed to the
internet — this runs entirely on your own machine).
"""
import sys
sys.path.insert(0, '.')

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from src.generators.scenario_generator import generate_scenario
from src.algorithms.fifo import FIFOScheduler
from src.algorithms.greedy import PriorityGreedyScheduler
from src.evaluators.metrics import compute_metrics

st.set_page_config(page_title="EOS Baseline Scheduler", layout="wide")
st.title("Earth Observation Constellation Scheduler — Demo")
st.caption("NASRDA Mission Planning Division — reproducible baseline framework")

# ---- Sidebar controls ----
st.sidebar.header("Scenario parameters")
n_satellites = st.sidebar.slider("Number of satellites", 1, 12, 2)
n_tasks = st.sidebar.slider("Number of observation requests", 5, 1000, 25)
seed = st.sidebar.number_input("Random seed", value=1, step=1)
show_alg = st.sidebar.selectbox("Algorithm to inspect in detail", ["Greedy-P", "Greedy-PW", "FIFO"])
run_button = st.sidebar.button("Run scenario", type="primary")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Change any parameter and click Run to generate a new synthetic scenario "
    "and compare FIFO, Greedy-P, and Greedy-PW on it."
)


def run_all_algorithms(satellites, requests, n_sats):
    buckets = [[] for _ in range(n_sats)]
    for i, r in enumerate(requests):
        buckets[i % n_sats].append(r)

    algorithms = {
        "FIFO": lambda sid: FIFOScheduler(sat_id=sid),
        "Greedy-P": lambda sid: PriorityGreedyScheduler(by_window_length=False, sat_id=sid),
        "Greedy-PW": lambda sid: PriorityGreedyScheduler(by_window_length=True, sat_id=sid),
    }

    all_results, schedules = {}, {}
    for name, factory in algorithms.items():
        scheduled_all, rejected_all, reasons_all, timeline = [], [], [], []
        for s_idx in range(n_sats):
            sched = factory(s_idx)
            sc, rj, rs = sched.schedule(buckets[s_idx], satellites)
            scheduled_all += sc
            rejected_all += rj
            reasons_all += rs
            sat = satellites[s_idx]
            current_time, current_angle = 0.0, 0.0
            sort_key = (lambda x: (-x.priority, x.window_length)) if name == "Greedy-PW" else \
                       (lambda x: (-x.priority, x.earliest_start)) if name == "Greedy-P" else None
            ordered = sorted(sc, key=sort_key) if sort_key else sc
            for req in ordered:
                slew = sat.slew_time(current_angle, req.roll_angle)
                start = max(current_time + slew, req.earliest_start)
                end = start + req.duration
                timeline.append({"satellite": s_idx, "request": req.id, "priority": req.priority,
                                  "start": start, "end": end})
                current_time, current_angle = end, req.roll_angle
        all_results[name] = compute_metrics(scheduled_all, rejected_all, 0.0, reasons_all, satellites[0])
        schedules[name] = timeline
    return all_results, schedules


if run_button or "results" not in st.session_state:
    satellites, requests = generate_scenario(n_satellites, n_tasks, seed=int(seed))
    results, schedules = run_all_algorithms(satellites, requests, n_satellites)
    st.session_state["results"] = results
    st.session_state["schedules"] = schedules
    st.session_state["n_satellites"] = n_satellites

results = st.session_state["results"]
schedules = st.session_state["schedules"]
n_sats_used = st.session_state["n_satellites"]

# ---- Summary table ----
st.subheader("Comparison summary")
summary_rows = []
for name, m in results.items():
    summary_rows.append({
        "Algorithm": name,
        "Total Priority": round(m["total_priority"], 1),
        "Scheduled": m["scheduled_count"],
        "Rejected": m["rejected_count"],
        "Completion Rate": f"{m['completion_rate']*100:.1f}%",
    })
st.table(pd.DataFrame(summary_rows).set_index("Algorithm"))

fifo_p = results["FIFO"]["total_priority"]
gp_p = results["Greedy-P"]["total_priority"]
if fifo_p > 0:
    improvement = 100 * (gp_p - fifo_p) / fifo_p
    st.metric("Greedy-P improvement over FIFO", f"{improvement:+.1f}%")

# ---- Timeline chart ----
st.subheader(f"Schedule timeline — {show_alg}")
timeline = schedules[show_alg]
if timeline:
    fig, ax = plt.subplots(figsize=(11, 1.2 + 0.6 * n_sats_used))
    colors = plt.cm.viridis_r
    for entry in timeline:
        ax.barh(entry["satellite"], entry["end"] - entry["start"], left=entry["start"],
                height=0.6, color=colors(entry["priority"] / 10), edgecolor="black", linewidth=0.3)
    ax.set_yticks(range(n_sats_used))
    ax.set_yticklabels([f"Satellite {i+1}" for i in range(n_sats_used)])
    ax.set_xlabel("Time (seconds)")
    sm = plt.cm.ScalarMappable(cmap=colors, norm=plt.Normalize(1, 10))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Priority", shrink=0.7)
    fig.tight_layout()
    st.pyplot(fig)
else:
    st.info("No requests were scheduled under this algorithm for this scenario.")

# ---- Raw schedule table ----
st.subheader("Schedule detail")
if timeline:
    df = pd.DataFrame(timeline).sort_values("start").reset_index(drop=True)
    df["satellite"] = df["satellite"].apply(lambda i: f"S{i+1}")
    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.caption(
    "Scenario parameters (slew rate, energy capacity, etc.) are drawn from published ranges "
    "typical of agile EO satellites in general, not from a specific NASRDA spacecraft, since "
    "one is not yet operational. Full limitations are discussed in Section 5.2 of the companion "
    "paper, \"A Reproducible Baseline Framework for Benchmarking Earth Observation Constellation "
    "Schedulers.\""
)
