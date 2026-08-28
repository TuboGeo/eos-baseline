"""Observation request class representing user-defined targets."""


class ObservationRequest:
    def __init__(self, req_id, lat, lon, priority, earliest_start, latest_end,
                 duration=10.0, roll_angle=0.0, energy=50.0, data=10.0):
        self.id = req_id
        self.lat = lat
        self.lon = lon
        self.priority = priority
        self.earliest_start = earliest_start
        self.latest_end = latest_end
        self.duration = duration
        self.roll_angle = roll_angle
        self.energy = energy
        self.data = data

    @property
    def window_length(self):
        return self.latest_end - self.earliest_start - self.duration

    def __repr__(self):
        return (f"Request({self.id}, priority={self.priority}, "
                f"lat={self.lat:.2f}, lon={self.lon:.2f})")
