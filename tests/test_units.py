"""Tests for sim.units and for the code that now uses it (issue #45)."""
import math
import re
from pathlib import Path

import numpy as np
import pytest

from sim import units
from sim.config import SimulationResults, TrackConfig
from sim.planning.sweep import run_fixed_speed_sweep

SIM_DIR = Path(__file__).resolve().parents[1] / "sim"


class TestKnownValues:
    @pytest.mark.parametrize(
        "func, arg, expected",
        [
            (units.mph_to_mps, 0, 0.0),
            (units.mph_to_mps, 2.237, 1.0),
            (units.mph_to_mps, 22.37, 10.0),
            (units.mps_to_mph, 0, 0.0),
            (units.mps_to_mph, 1, 2.237),
            (units.mps_to_mph, 10, 22.37),
            (units.meters_to_miles, 0, 0.0),
            (units.meters_to_miles, 1609.34, 1.0),
            (units.meters_to_miles, 3218.68, 2.0),
            (units.meters_to_km, 0, 0.0),
            (units.meters_to_km, 1000, 1.0),
            (units.meters_to_km, 604, 0.604),
            (units.km_to_meters, 0, 0.0),
            (units.km_to_meters, 1, 1000.0),
            (units.km_to_meters, 4.989, 4989.0),
            (units.minutes_to_hours, 0, 0.0),
            (units.minutes_to_hours, 60, 1.0),
            (units.minutes_to_hours, 1, 1 / 60),
            (units.minutes_to_hours, 90, 1.5),
            (units.minutes_to_seconds, 0, 0.0),
            (units.minutes_to_seconds, 1, 60.0),
            (units.minutes_to_seconds, 2.5, 150.0),
        ],
    )
    def test_conversion(self, func, arg, expected):
        assert func(arg) == pytest.approx(expected)

    def test_negative_values_convert_linearly(self):
        assert units.mps_to_mph(-5) == pytest.approx(-units.mps_to_mph(5))
        assert units.minutes_to_hours(-30) == pytest.approx(-0.5)


class TestRoundTrips:
    @pytest.mark.parametrize("value", [0.0, 0.1, 1.0, 15.0, 33.6, 1234.5])
    def test_speed(self, value):
        assert units.mps_to_mph(units.mph_to_mps(value)) == pytest.approx(value)
        assert units.mph_to_mps(units.mps_to_mph(value)) == pytest.approx(value)

    @pytest.mark.parametrize("value", [0.0, 0.604, 1.77, 4.989, 250.0])
    def test_km_meters(self, value):
        assert units.meters_to_km(units.km_to_meters(value)) == pytest.approx(value)


class TestInputKinds:
    def test_numpy_arrays_convert_elementwise(self):
        speeds = np.array([0.0, 10.0, 20.0])
        np.testing.assert_allclose(units.mps_to_mph(speeds), speeds * 2.237)
        assert isinstance(units.mps_to_mph(speeds), np.ndarray)

    def test_ints_floats_and_numpy_scalars(self):
        for value in (10, 10.0, np.float64(10.0), np.int64(10)):
            assert units.mps_to_mph(value) == pytest.approx(22.37)

    def test_inputs_are_not_mutated(self):
        speeds = np.array([1.0, 2.0])
        units.mps_to_mph(speeds)
        np.testing.assert_array_equal(speeds, [1.0, 2.0])

    def test_nan_and_inf_propagate(self):
        assert math.isnan(units.mph_to_mps(float("nan")))
        assert math.isinf(units.meters_to_km(float("inf")))


class TestConstants:
    """Pin the constants so display values stay what they were before the refactor."""

    def test_values(self):
        assert units.MPH_PER_MPS == 2.237
        assert units.METERS_PER_MILE == 1609.34
        assert units.METERS_PER_KM == 1000.0
        assert units.SECONDS_PER_MINUTE == 60.0
        assert units.MINUTES_PER_HOUR == 60.0

    def test_mph_and_mps_are_inverses_of_the_same_constant(self):
        assert units.mph_to_mps(units.MPH_PER_MPS) == pytest.approx(1.0)


class TestCallersUseTheHelpers:
    def _results(self, speed, distance_m):
        n = len(speed)
        zeros = np.zeros(n)
        return SimulationResults(
            time_minutes=np.arange(n, dtype=float), soc=np.linspace(1, 0.5, n),
            speed=np.asarray(speed, dtype=float), ghi=zeros, cloud_cover=zeros,
            lap_times=[], total_laps=0, total_distance_m=distance_m, bdr=zeros,
            ideal_soc=zeros, completed_full_window=True,
            reached_min_soc_time_minutes=None, laps_at_min_soc=None,
        )

    def test_results_distance_and_speed_properties(self):
        r = self._results([10.0, 20.0, 30.0], 16093.4)
        assert r.total_distance_km == pytest.approx(16.0934)
        assert r.total_distance_miles == pytest.approx(10.0)
        assert r.avg_speed_mph == pytest.approx(20.0 * 2.237)
        assert r.max_speed_mph == pytest.approx(30.0 * 2.237)
        assert r.min_speed_mph == pytest.approx(10.0 * 2.237)

    def test_track_lap_distance_km(self):
        track = TrackConfig(
            name="t", file_path_name="t", location="x", latitude=0, longitude=0,
            lap_distance_m=1770.0, timezone="UTC",
        )
        assert track.lap_distance_km == pytest.approx(1.77)

    def test_sweep_converts_mph_to_commanded_mps(self, monkeypatch):
        seen = []

        class FakeSim:
            def __init__(self, track, car, race, use_api_weather=True, synthetic_weather_seed=None):
                seen.append(race.fixed_speed_mps)

            def run(self):
                raise StopIteration

        monkeypatch.setattr("sim.planning.sweep.LapsRaceSimulator", FakeSim)
        from sim.config import RaceConfig
        with pytest.raises(StopIteration):
            run_fixed_speed_sweep(
                track=None, car=None, base_race=RaceConfig(), speeds_mph=[22], use_api_weather=False
            )
        assert seen == [pytest.approx(22 / 2.237)]


class TestNoDuplicatedLiterals:
    """Acceptance criterion: repeated unit constants live only in sim/units.py."""

    @pytest.mark.parametrize("literal", [r"\b2\.237\b", r"\b1609\.34\b"])
    def test_literal_only_in_units_module(self, literal):
        offenders = [
            str(p.relative_to(SIM_DIR.parent))
            for p in SIM_DIR.rglob("*.py")
            if p.name != "units.py" and re.search(literal, p.read_text())
        ]
        assert offenders == []
