"""Random scenario generator for creating test instances."""
import random
from ..core.satellite import Satellite
from ..core.request import ObservationRequest


def generate_scenario(num_satellites, num_requests, seed=42, time_horizon=7200.0):
    random.seed(seed)

    satellites = []
    for i in range(num_satellites):
        satellites.append(Satellite(
            sat_id=f"S{i+1:03d}",
            max_rate=random.uniform(2.0, 4.0),
            max_accel=random.uniform(0.3, 0.7),
            settle_time=random.uniform(2.0, 5.0),
            energy_cap=random.uniform(400.0, 600.0),
            storage_cap=random.uniform(150.0, 250.0),
            kappa=random.uniform(0.005, 0.015)
        ))

    requests = []
    for i in range(num_requests):
        start = random.uniform(0, time_horizon * 0.7)
        duration = random.uniform(5.0, 20.0)
        end = start + duration + random.uniform(30.0, 300.0)
        requests.append(ObservationRequest(
            req_id=f"R{i+1:04d}",
            lat=random.uniform(-90.0, 90.0),
            lon=random.uniform(-180.0, 180.0),
            priority=random.randint(1, 10),
            earliest_start=start,
            latest_end=min(end, time_horizon),
            duration=duration,
            roll_angle=random.uniform(-45.0, 45.0),
            energy=random.uniform(30.0, 70.0),
            data=random.uniform(5.0, 15.0)
        ))

    return satellites, requests
