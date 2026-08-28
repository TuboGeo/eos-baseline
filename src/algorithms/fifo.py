"""First-In-First-Out scheduling algorithm."""
from .base import Scheduler


class FIFOScheduler(Scheduler):
    def __init__(self, sat_id=0, use_constant_rate=False):
        self.sat_id = sat_id
        self.use_constant_rate = use_constant_rate

    def schedule(self, requests, satellites):
        sat = satellites[self.sat_id]
        scheduled = []
        rejected = []
        rejection_reasons = []
        current_time = 0.0
        current_angle = 0.0
        energy_remaining = sat.energy_cap
        storage_remaining = sat.storage_cap

        for req in requests:
            if self.use_constant_rate:
                slew = sat.slew_time_constant_rate(current_angle, req.roll_angle)
            else:
                slew = sat.slew_time(current_angle, req.roll_angle)
            feasible_start = current_time + slew
            start_time = max(feasible_start, req.earliest_start)
            end_time = start_time + req.duration

            if end_time > req.latest_end:
                rejected.append(req)
                rejection_reasons.append("WINDOW_VIOLATION")
            elif energy_remaining < req.energy:
                rejected.append(req)
                rejection_reasons.append("ENERGY_EXHAUSTED")
            elif storage_remaining < req.data:
                rejected.append(req)
                rejection_reasons.append("STORAGE_EXHAUSTED")
            else:
                scheduled.append(req)
                current_time = end_time
                current_angle = req.roll_angle
                energy_remaining -= req.energy
                storage_remaining -= req.data
                rejection_reasons.append("SCHEDULED")

        return scheduled, rejected, rejection_reasons
