"""Tests for deterministic synthetic weather (no network access)."""
from types import SimpleNamespace

import numpy as np
import pytest

from sim.weather import DEFAULT_SYNTHETIC_SEED, WeatherService, _moving_average


def race(start=10.0, end=18.0):
    return SimpleNamespace(start_time_hour=start, end_time_hour=end)


@pytest.fixture
def service(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("synthetic weather must not touch the network")

    monkeypatch.setattr(WeatherService, "fetch_weather_data", no_network)
    monkeypatch.setattr(WeatherService, "client", property(no_network))
    return WeatherService(track=None)


def assert_same(a, b):
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x, y)


class TestDeterminism:
    def test_repeated_calls_return_same_arrays(self, service):
        assert_same(service.generate_synthetic_data(race()), service.generate_synthetic_data(race()))

    def test_separate_service_instances_agree(self, service):
        other = WeatherService(track=None)
        assert_same(service.generate_synthetic_data(race()), other.generate_synthetic_data(race()))

    def test_default_seed_matches_explicit_default(self, service):
        assert_same(
            service.generate_synthetic_data(race()),
            service.generate_synthetic_data(race(), seed=DEFAULT_SYNTHETIC_SEED),
        )

    def test_different_seeds_differ(self, service):
        _, ghi_a, cloud_a = service.generate_synthetic_data(race(), seed=1)
        _, ghi_b, cloud_b = service.generate_synthetic_data(race(), seed=2)
        assert not np.array_equal(ghi_a, ghi_b)
        assert not np.array_equal(cloud_a, cloud_b)

    def test_same_seed_is_reproducible_across_many_calls(self, service):
        first = service.generate_synthetic_data(race(), seed=123)
        for _ in range(5):
            assert_same(first, service.generate_synthetic_data(race(), seed=123))

    def test_ignores_global_numpy_random_state(self, service):
        np.random.seed(0)
        a = service.generate_synthetic_data(race())
        np.random.seed(999)
        np.random.rand(50)
        b = service.generate_synthetic_data(race())
        assert_same(a, b)

    def test_does_not_consume_global_numpy_random_state(self, service):
        np.random.seed(42)
        expected = np.random.rand(3)
        np.random.seed(42)
        service.generate_synthetic_data(race())
        np.testing.assert_array_equal(np.random.rand(3), expected)

    def test_input_race_config_not_mutated(self, service):
        r = race()
        service.generate_synthetic_data(r)
        assert (r.start_time_hour, r.end_time_hour) == (10.0, 18.0)

    def test_matches_legacy_global_seed_stream(self, service):
        """Seed 7 reproduces the output the sweeps got from np.random.seed(7) before this change."""
        np.random.seed(7)
        start, end = 600, 1080
        t = np.arange(start, end)
        a = 900 / ((780 - start) ** 2)
        ghi = np.maximum(0, -a * (t - 780) ** 2 + 900)
        noise = np.clip(np.random.normal(1.0, 0.1, len(ghi)), 0.7, 1.2)
        ghi = ghi * np.convolve(noise, np.ones(15) / 15, mode="same")
        cloud = np.clip(0.3 + 0.3 * np.random.randn(len(t)), 0, 1)
        cloud = np.convolve(cloud, np.ones(30) / 30, mode="same")

        _, got_ghi, got_cloud = service.generate_synthetic_data(race(), seed=7)
        np.testing.assert_allclose(got_ghi, ghi)
        np.testing.assert_allclose(got_cloud, cloud)


class TestShapeAndRange:
    def test_array_lengths_match_race_window(self, service):
        t, ghi, cloud = service.generate_synthetic_data(race(10.0, 18.0))
        assert len(t) == len(ghi) == len(cloud) == 8 * 60

    def test_time_axis_is_minutes_of_day(self, service):
        t, _, _ = service.generate_synthetic_data(race(9.0, 17.0))
        assert t[0] == 9 * 60
        assert t[-1] == 17 * 60 - 1
        assert np.all(np.diff(t) == 1)

    def test_ghi_nonnegative_and_finite(self, service):
        _, ghi, cloud = service.generate_synthetic_data(race())
        assert np.all(np.isfinite(ghi)) and np.all(np.isfinite(cloud))
        assert ghi.min() >= 0

    def test_cloud_cover_within_unit_interval(self, service):
        for seed in range(20):
            _, _, cloud = service.generate_synthetic_data(race(), seed=seed)
            assert cloud.min() >= 0 and cloud.max() <= 1

    def test_ghi_peaks_near_solar_noon(self, service):
        t, ghi, _ = service.generate_synthetic_data(race())
        assert abs(t[np.argmax(ghi)] - 13 * 60) < 60
        assert ghi.max() <= 900 * 1.2 + 1e-9

    def test_returns_numpy_arrays(self, service):
        for arr in service.generate_synthetic_data(race()):
            assert isinstance(arr, np.ndarray)


class TestEdgeCases:
    def test_start_at_solar_noon_does_not_divide_by_zero(self, service):
        t, ghi, cloud = service.generate_synthetic_data(race(13.0, 18.0))
        assert len(t) == len(ghi) == len(cloud) == 5 * 60
        assert np.all(np.isfinite(ghi))

    def test_start_after_solar_noon(self, service):
        t, ghi, cloud = service.generate_synthetic_data(race(14.0, 18.0))
        assert len(ghi) == len(cloud) == len(t) == 4 * 60
        assert np.all(np.isfinite(ghi)) and ghi.min() >= 0

    @pytest.mark.parametrize("minutes", [1, 2, 5, 14, 15, 16, 29, 30, 31])
    def test_short_windows_keep_matching_lengths(self, service, minutes):
        r = race(10.0, 10.0 + minutes / 60)
        t, ghi, cloud = service.generate_synthetic_data(r)
        assert len(t) == len(ghi) == len(cloud) == minutes

    def test_empty_window_raises_clear_error(self, service):
        with pytest.raises(ValueError, match="at least one minute"):
            service.generate_synthetic_data(race(10.0, 10.0))

    def test_reversed_window_raises_clear_error(self, service):
        with pytest.raises(ValueError, match="at least one minute"):
            service.generate_synthetic_data(race(18.0, 10.0))

    def test_sub_minute_window_raises(self, service):
        with pytest.raises(ValueError):
            service.generate_synthetic_data(race(10.0, 10.0 + 0.5 / 60))

    def test_fractional_hours(self, service):
        t, ghi, _ = service.generate_synthetic_data(race(9.5, 17.25))
        assert t[0] == 570 and len(ghi) == 17 * 60 + 15 - 9 * 60 - 30

    def test_full_day_window(self, service):
        t, ghi, cloud = service.generate_synthetic_data(race(0.0, 24.0))
        assert len(t) == len(ghi) == len(cloud) == 1440
        assert np.all(np.isfinite(ghi))

    def test_seed_zero_is_valid_and_not_treated_as_missing(self, service):
        a = service.generate_synthetic_data(race(), seed=0)
        b = service.generate_synthetic_data(race(), seed=DEFAULT_SYNTHETIC_SEED)
        assert not np.array_equal(a[1], b[1])


class TestMovingAverage:
    @pytest.mark.parametrize("n,w", [(100, 15), (30, 30), (31, 30), (50, 30), (200, 15)])
    def test_matches_numpy_same_when_long_enough(self, n, w):
        x = np.random.RandomState(0).rand(n)
        np.testing.assert_allclose(
            _moving_average(x, w), np.convolve(x, np.ones(w) / w, mode="same")
        )

    @pytest.mark.parametrize("n", [1, 2, 7, 14])
    def test_output_length_for_short_input(self, n):
        assert len(_moving_average(np.ones(n), 15)) == n

    def test_constant_signal_interior_unchanged(self):
        out = _moving_average(np.full(100, 2.0), 15)
        np.testing.assert_allclose(out[10:-10], 2.0)


class TestSimulatorIntegration:
    """End to end: an offline run is reproducible, and the seed reaches the weather."""

    def _run(self, capsys, seed=None):
        from sim.config import CarConfig, RaceConfig, TrackConfig
        from sim.simulator import LapsRaceSimulator

        track = TrackConfig.from_json("courses/shenandoah_speedway.json")
        car = CarConfig.from_json("car_params.json")
        kwargs = {} if seed is None else {"synthetic_weather_seed": seed}
        sim = LapsRaceSimulator(
            track=track, car=car, race=RaceConfig(strategy="fixed"), use_api_weather=False, **kwargs
        )
        results = sim.run()
        capsys.readouterr()
        return results

    def test_offline_run_is_reproducible(self, capsys):
        a, b = self._run(capsys), self._run(capsys)
        np.testing.assert_array_equal(a.soc, b.soc)
        assert a.total_laps == b.total_laps

    def test_explicit_seed_is_reproducible(self, capsys):
        a, b = self._run(capsys, seed=3), self._run(capsys, seed=3)
        np.testing.assert_array_equal(a.soc, b.soc)
