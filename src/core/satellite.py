"""Satellite class representing the physical and operational parameters
of an Earth Observation satellite."""


class Satellite:
    def __init__(self, sat_id, max_rate=3.0, max_accel=0.5, settle_time=3.0,
                 energy_cap=500.0, storage_cap=200.0, kappa=0.01):
        self.id = sat_id
        self.max_rate = max_rate
        self.max_accel = max_accel
        self.settle_time = settle_time
        self.energy_cap = energy_cap
        self.storage_cap = storage_cap
        self.kappa = kappa

    def slew_time(self, angle_a, angle_b):
        """Kinematic slew time model (Section 2.3 of the paper): triangular
        profile below the critical angle, trapezoidal profile above it.
        Corrected for continuity at the critical angle (see verification note)."""
        delta = abs(angle_b - angle_a)
        critical = (self.max_rate ** 2) / self.max_accel
        if delta <= critical:
            # Triangular profile: accelerate then immediately decelerate,
            # peak velocity sqrt(delta * max_accel) never exceeds max_rate.
            slew_duration = 2 * (delta / self.max_accel) ** 0.5
        else:
            # Trapezoidal profile: accelerate to max_rate, coast, decelerate.
            accel_time = self.max_rate / self.max_accel
            coast_distance = delta - critical
            coast_time = coast_distance / self.max_rate
            slew_duration = 2 * accel_time + coast_time
        return slew_duration + self.settle_time

    def slew_time_constant_rate(self, angle_a, angle_b):
        """Naive constant-angular-rate model (no acceleration limit),
        used as the comparison baseline in Section 4.2.4."""
        delta = abs(angle_b - angle_a)
        return delta / self.max_rate + self.settle_time

    def slew_energy(self, angle_a, angle_b):
        return self.kappa * abs(angle_b - angle_a)
