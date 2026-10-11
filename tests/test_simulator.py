import numpy as np
import pytest
from types import SimpleNamespace

from sim.simulator import LapsRaceSimulator


class FakePhysics:
    def solar_power(self, ghi):
        return 0.0

    def power_drained(self, speed):
        return 0.0

    def battery_drain_rate(self, speed, ghi):
        return 0.0

    def regen_energy(self, prev_speed, speed):
        return 0.0


class FakeWeather:
    def generate_synthetic_data(self, race):
        return (
            np.array([0.0, 1.0]),
            np.array([0.0, 0.0]),
            np.array([0.0, 0.0]),
        )


class FakeStrategy:
    def __init__(self, optimal_speed):
        self.optimal_speed = optimal_speed
        self.ideal_soc = np.array([1.0, 1.0])

    def prepare(self, physics, ghi_data, cloud_data, dt_hours):
        pass

    def next_speed(self, i, *args):
        return self.optimal_speed


def make_simulator(lap_distance_m=1000.0, time_step_minutes=1.0,
                   optimal_speed=25.0):
    """Build a simulator with fake dependencies so lap counting is isolated."""
    simulator = LapsRaceSimulator.__new__(LapsRaceSimulator)

    simulator.track = SimpleNamespace(lap_distance_m=lap_distance_m)
    simulator.car = SimpleNamespace(battery_capacity=1_000_000.0)
    simulator.race = SimpleNamespace(
        time_step_minutes=time_step_minutes,
        start_soc=1.0,
        min_soc=0.0,
        strategy="test",
    )
    simulator.use_api_weather = False
    simulator.physics = FakePhysics()
    simulator.weather = FakeWeather()
    simulator.strategy = FakeStrategy(optimal_speed)

    return simulator


def test_counts_multiple_laps_in_one_timestep():
    """Each timestep covers several full laps, and every lap is counted."""
    simulator = make_simulator(
        lap_distance_m=1000.0,
        time_step_minutes=1.0,
        optimal_speed=50.0,
    )

    # The run has two 1-minute timesteps. At 50 m/s, each timestep covers
    # 3000 m, which is exactly 3 laps, so 6 laps in total.
    results = simulator.run()

    assert results.total_laps == 6

    # Each lap is 1000 m at 50 m/s = 20 s = 1/3 min, including the laps
    # that finish within the same timestep.
    assert results.lap_times == pytest.approx([1 / 3] * 6)


def test_partial_lap_distance_carries_over():
    """Distance left after full laps carries into the next timestep."""
    simulator = make_simulator(
        lap_distance_m=1000.0,
        time_step_minutes=1.0,
        optimal_speed=2500.0 / 60.0,
    )

    # Timestep 1: 2500 m -> 2 laps + 500 m leftover.
    # Change speed for timestep 2 so it travels 600 m.
    simulator.strategy.next_speed = lambda i, *args: 10.0

    results = simulator.run()

    # The 500 m leftover plus the next 600 m completes a third lap.
    assert results.total_laps == 3

    # Lap durations in minutes:
    # Laps 1 and 2 finish at 24 s and 48 s, so each takes 24 s = 0.4 min.
    # Lap 3 starts at 48 s. It finishes at 60 s + 50 s (the 500 m still
    # needed at 10 m/s) = 110 s, so it takes 62 s.
    assert results.lap_times == pytest.approx([0.4, 0.4, 62 / 60])


def test_one_lap_at_a_time_still_works():
    """Normal timesteps covering one lap still count one lap each."""
    simulator = make_simulator(
        lap_distance_m=1000.0,
        time_step_minutes=1.0,
        optimal_speed=1000.0 / 60.0,
    )

    results = simulator.run()

    assert results.total_laps == 2
    assert results.lap_times == pytest.approx([1.0, 1.0])