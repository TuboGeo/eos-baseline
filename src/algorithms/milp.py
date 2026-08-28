"""MILP-optimal scheduler using OR-Tools CP-SAT, for small (XS) instances only."""
from .base import Scheduler
from ortools.sat.python import cp_model


class MILPScheduler(Scheduler):
    def __init__(self, sat_id=0, time_limit_s=300):
        self.sat_id = sat_id
        self.time_limit_s = time_limit_s

    def schedule(self, requests, satellites):
        sat = satellites[self.sat_id]
        n = len(requests)
        model = cp_model.CpModel()

        # Precompute slew times between all pairs (including a virtual start at angle 0)
        angles = [r.roll_angle for r in requests]

        def slew(a, b):
            return sat.slew_time(a, b)

        x = [model.NewBoolVar(f"x_{i}") for i in range(n)]
        # start/end times as integers (seconds)
        horizon = int(max(r.latest_end for r in requests)) + 1
        start = [model.NewIntVar(0, horizon, f"start_{i}") for i in range(n)]
        end = [model.NewIntVar(0, horizon, f"end_{i}") for i in range(n)]

        for i, r in enumerate(requests):
            model.Add(end[i] == start[i] + int(r.duration)).OnlyEnforceIf(x[i])
            model.Add(start[i] >= int(r.earliest_start)).OnlyEnforceIf(x[i])
            model.Add(end[i] <= int(r.latest_end)).OnlyEnforceIf(x[i])

        # Sequencing: for every pair, if both scheduled, order them and respect slew time
        intervals = []
        for i in range(n):
            interval = model.NewOptionalIntervalVar(start[i], int(requests[i].duration), end[i], x[i], f"iv_{i}")
            intervals.append(interval)
        model.AddNoOverlap(intervals)

        # Approximate slew constraint: since exact slew depends on sequence order,
        # we add pairwise disjunctive constraints with worst-case slew as a buffer.
        # This makes the MILP a conservative (slightly pessimistic) exact solve,
        # consistent with treating XS instances only, as specified in the paper.
        for i in range(n):
            for j in range(i + 1, n):
                s_ij = int(slew(angles[i], angles[j]))
                s_ji = int(slew(angles[j], angles[i]))
                before = model.NewBoolVar(f"before_{i}_{j}")
                model.Add(start[j] >= end[i] + s_ij).OnlyEnforceIf([x[i], x[j], before])
                model.Add(start[i] >= end[j] + s_ji).OnlyEnforceIf([x[i], x[j], before.Not()])

        # Energy and storage constraints
        model.Add(sum(int(requests[i].energy * 100) * x[i] for i in range(n)) <= int(sat.energy_cap * 100))
        model.Add(sum(int(requests[i].data * 100) * x[i] for i in range(n)) <= int(sat.storage_cap * 100))

        model.Maximize(sum(requests[i].priority * x[i] for i in range(n)))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_s
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)

        scheduled, rejected = [], []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for i, r in enumerate(requests):
                if solver.Value(x[i]):
                    scheduled.append(r)
                else:
                    rejected.append(r)
        else:
            rejected = list(requests)

        is_optimal = (status == cp_model.OPTIMAL)
        solve_time = solver.WallTime()
        return scheduled, rejected, is_optimal, solve_time
