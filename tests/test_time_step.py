"""Tests for the configurable simulation time step (issue #8)."""
import sys
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from sim import main as cli
from sim.config import CarConfig, RaceConfig, get_available_tracks
from sim.controllers import IntervalHoldStrategy
from sim.simulator import LapsRaceSimulator
from sim.weather import WeatherService, resample_to_time_step

STRATEGIES = ["fixed", "pi", "stepped", "interval-hold"]
WINDOW_MINUTES = 480  # default race window: 10:00-18:00


@pytest.fixture(scope="module")
def track():
    return get_available_tracks()[0]


def one_minute_weather(n=60):
    t = np.arange(600, 600 + n, dtype=float)
    ghi = np.arange(n, dtype=float)
    cloud = np.linspace(0.0, 1.0, n)
    return t, ghi, cloud


def run_sim(track, step, strategy="fixed", car=None, seed=1, **race_kwargs):
    np.random.seed(seed)
    race = RaceConfig(strategy=strategy, time_step_minutes=step, **race_kwargs)
    sim = LapsRaceSimulator(track, car or CarConfig(), race, use_api_weather=False)
    return sim.run()


# A battery big enough that the car never hits min SoC, so the whole window runs.
BIG_BATTERY = CarConfig(battery_capacity=1_000_000)


class TestResample:
    def test_one_minute_step_is_unchanged(self):
        t, g, c = one_minute_weather()
        t2, g2, c2 = resample_to_time_step(t, g, c, 1.0)
        np.testing.assert_array_equal(t, t2)
        np.testing.assert_array_equal(g, g2)
        np.testing.assert_array_equal(c, c2)

    def test_coarse_step_averages_each_block(self):
        t, g, c = one_minute_weather(10)  # ghi 0..9
        t2, g2, _ = resample_to_time_step(t, g, c, 5.0)
        np.testing.assert_array_equal(t2, [600.0, 605.0])
        np.testing.assert_allclose(g2, [2.0, 7.0])  # mean(0..4), mean(5..9)

    @pytest.mark.parametrize("step", [2, 3, 5, 10, 15, 60])
    def test_coarse_step_preserves_mean_when_divisible(self, step):
        t, g, c = one_minute_weather(60)
        _, g2, c2 = resample_to_time_step(t, g, c, float(step))
        assert g2.mean() == pytest.approx(g.mean())
        assert c2.mean() == pytest.approx(c.mean())

    @pytest.mark.parametrize("step", [2.0, 5.0, 7.0, 10.0, 0.5, 0.25])
    def test_spacing_equals_step(self, step):
        t, g, c = one_minute_weather(60)
        t2, _, _ = resample_to_time_step(t, g, c, step)
        np.testing.assert_allclose(np.diff(t2), step)

    @pytest.mark.parametrize("step", [2.0, 5.0, 7.0, 0.5])
    def test_starts_at_first_timestamp(self, step):
        t, g, c = one_minute_weather()
        t2, _, _ = resample_to_time_step(t, g, c, step)
        assert t2[0] == t[0]

    def test_non_divisible_step_keeps_partial_last_block(self):
        t, g, c = one_minute_weather(10)
        t2, g2, _ = resample_to_time_step(t, g, c, 7.0)
        np.testing.assert_array_equal(t2, [600.0, 607.0])
        np.testing.assert_allclose(g2, [3.0, 8.0])  # mean(0..6), mean(7..9)

    def test_fractional_step_never_produces_nan(self):
        # step 5.5 over 6 samples would leave an empty trailing bin
        t, g, c = one_minute_weather(6)
        t2, g2, c2 = resample_to_time_step(t, g, c, 5.5)
        assert not np.isnan(g2).any() and not np.isnan(c2).any()
        assert len(t2) == len(g2) == len(c2)

    @pytest.mark.parametrize("n", [1, 2, 7, 59, 480])
    @pytest.mark.parametrize("step", [1.5, 2.0, 3.3, 5.0, 9.0, 480.0, 1000.0])
    def test_output_is_finite_and_aligned(self, n, step):
        t, g, c = one_minute_weather(n)
        t2, g2, c2 = resample_to_time_step(t, g, c, step)
        assert len(t2) == len(g2) == len(c2) >= 1
        assert np.isfinite(g2).all() and np.isfinite(c2).all()

    def test_fine_step_interpolates_linearly(self):
        t, g, c = one_minute_weather(10)
        t2, g2, _ = resample_to_time_step(t, g, c, 0.5)
        np.testing.assert_allclose(g2[:5], [0.0, 0.5, 1.0, 1.5, 2.0])
        assert len(t2) == 20

    def test_constant_weather_stays_constant(self):
        t = np.arange(600, 660, dtype=float)
        g = np.full(60, 750.0)
        c = np.full(60, 0.25)
        for step in (0.5, 2.0, 7.0):
            _, g2, c2 = resample_to_time_step(t, g, c, step)
            np.testing.assert_allclose(g2, 750.0)
            np.testing.assert_allclose(c2, 0.25)


class TestSyntheticWeatherUsesStep:
    @pytest.mark.parametrize("step", [0.5, 1.0, 2.0, 5.0, 10.0, 15.0])
    def test_shape_and_spacing(self, track, step):
        np.random.seed(0)
        race = RaceConfig(time_step_minutes=step)
        t, ghi, cloud = WeatherService(track).generate_synthetic_data(race)
        assert len(t) == len(ghi) == len(cloud)
        np.testing.assert_allclose(np.diff(t), step)
        assert len(t) == pytest.approx(WINDOW_MINUTES / step, abs=1)
        assert t[0] == 600

    def test_default_matches_previous_one_minute_behavior(self, track):
        np.random.seed(0)
        t, _, _ = WeatherService(track).generate_synthetic_data(RaceConfig())
        np.testing.assert_array_equal(t, np.arange(600, 1080))

    def test_values_stay_physical(self, track):
        for step in (1.0, 5.0, 15.0):
            np.random.seed(3)
            _, ghi, cloud = WeatherService(track).generate_synthetic_data(
                RaceConfig(time_step_minutes=step)
            )
            assert (ghi >= 0).all()
            assert (cloud >= 0).all() and (cloud <= 1).all()


class TestApiWeatherUsesStep:
    """Exercise fetch_weather_data with a fake Open-Meteo client."""

    @staticmethod
    def fake_client(track):
        today = pd.Timestamp.now(tz=track.timezone).normalize()
        start = today.tz_convert("UTC")
        hours = 24 * 16
        ghi = np.array([max(0.0, 800 - 40 * abs((h % 24) - 13) ** 1.5) for h in range(hours)], dtype=np.float32)
        cloud = np.full(hours, 50.0, dtype=np.float32)

        def variable(values):
            return SimpleNamespace(ValuesAsNumpy=lambda: values)

        hourly = SimpleNamespace(
            Time=lambda: int(start.timestamp()),
            TimeEnd=lambda: int((start + pd.Timedelta(hours=hours)).timestamp()),
            Interval=lambda: 3600,
            Variables=lambda i: variable([ghi, cloud][i]),
        )
        response = SimpleNamespace(Hourly=lambda: hourly)
        return SimpleNamespace(weather_api=lambda url, params=None: [response])

    @pytest.mark.parametrize("step", [1.0, 5.0, 15.0])
    def test_resampled_to_step(self, track, step):
        service = WeatherService(track)
        service._client = self.fake_client(track)
        t, ghi, cloud = service.fetch_weather_data(RaceConfig(time_step_minutes=step))
        np.testing.assert_allclose(np.diff(t), step)
        assert len(t) == len(ghi) == len(cloud) == pytest.approx(WINDOW_MINUTES / step, abs=1)
        np.testing.assert_allclose(cloud, 0.5)

    def test_energy_is_consistent_across_steps(self, track):
        service = WeatherService(track)
        service._client = self.fake_client(track)
        totals = []
        for step in (1.0, 5.0, 10.0):
            t, ghi, _ = service.fetch_weather_data(RaceConfig(time_step_minutes=step))
            totals.append(ghi.sum() * step)  # W/m^2 * minutes
        assert totals[1] == pytest.approx(totals[0], rel=1e-6)
        assert totals[2] == pytest.approx(totals[0], rel=1e-6)


class TestRaceConfigValidation:
    @pytest.mark.parametrize("bad", [0, -1, -0.5])
    def test_non_positive_rejected(self, bad):
        with pytest.raises(ValueError, match="Time step must be greater than 0."):
            RaceConfig(time_step_minutes=bad)

    @pytest.mark.parametrize("ok", [0.1, 1, 2.5, 60])
    def test_positive_accepted(self, ok):
        assert RaceConfig(time_step_minutes=ok).time_step_minutes == ok


class TestSimulatorIsStepIndependent:
    """The core bug: changing the step must not change the race being simulated."""

    STEPS = [0.5, 1.0, 2.0, 5.0, 10.0]

    @pytest.mark.parametrize("step", STEPS)
    def test_time_axis_spans_the_window(self, track, step):
        r = run_sim(track, step, car=BIG_BATTERY)
        span = r.time_minutes[-1] - r.time_minutes[0]
        assert span == pytest.approx(WINDOW_MINUTES - step, abs=step)
        assert r.completed_full_window

    @pytest.mark.parametrize("step", STEPS)
    def test_number_of_steps_scales_inversely(self, track, step):
        r = run_sim(track, step, car=BIG_BATTERY)
        assert len(r.time_minutes) == pytest.approx(WINDOW_MINUTES / step, abs=1)

    @pytest.mark.parametrize("step", STEPS)
    def test_time_axis_spacing_matches_step(self, track, step):
        r = run_sim(track, step, car=BIG_BATTERY)
        np.testing.assert_allclose(np.diff(r.time_minutes), step)

    @pytest.mark.parametrize("step", [0.5, 2.0, 5.0, 10.0])
    def test_distance_matches_one_minute_baseline(self, track, step):
        base = run_sim(track, 1.0, car=BIG_BATTERY)
        other = run_sim(track, step, car=BIG_BATTERY)
        assert other.total_distance_m == pytest.approx(base.total_distance_m, rel=0.02)

    @pytest.mark.parametrize("step", [0.5, 2.0, 5.0, 10.0])
    def test_distance_matches_baseline_when_battery_limited(self, track, step):
        base = run_sim(track, 1.0)  # default battery runs out mid-race
        other = run_sim(track, step)
        assert other.total_distance_m == pytest.approx(base.total_distance_m, rel=0.03)
        assert other.final_soc == pytest.approx(base.final_soc, abs=0.01)

    @pytest.mark.parametrize("step", [2.0, 5.0, 10.0])
    def test_time_of_reaching_min_soc_matches_baseline(self, track, step):
        base = run_sim(track, 1.0)
        other = run_sim(track, step)
        assert base.reached_min_soc_time_minutes is not None
        assert other.reached_min_soc_time_minutes == pytest.approx(
            base.reached_min_soc_time_minutes, abs=2 * step
        )

    def test_default_step_results_unchanged_from_one_minute(self, track):
        np.random.seed(1)
        implicit = LapsRaceSimulator(
            track, CarConfig(), RaceConfig(strategy="fixed"), use_api_weather=False
        ).run()
        explicit = run_sim(track, 1.0)
        np.testing.assert_array_equal(implicit.soc, explicit.soc)
        np.testing.assert_array_equal(implicit.time_minutes, explicit.time_minutes)


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("step", [1.0, 2.0, 5.0, 10.0])
class TestEveryStrategyAtEveryStep:
    def test_runs_with_sane_outputs(self, track, strategy, step):
        r = run_sim(track, step, strategy)
        for arr in (r.soc, r.speed, r.time_minutes, r.ghi, r.bdr):
            assert np.isfinite(arr).all()
        assert (r.soc >= 0).all() and (r.soc <= 1).all()
        assert (r.speed > 0).all()
        assert r.total_distance_m > 0
        assert len(r.soc) == len(r.time_minutes) == len(r.speed)

    def test_distance_close_to_one_minute_run(self, track, strategy, step):
        base = run_sim(track, 1.0, strategy)
        other = run_sim(track, step, strategy)
        # Controllers react per step, so allow a looser band than the fixed strategy.
        assert other.total_distance_m == pytest.approx(base.total_distance_m, rel=0.10)


class TestIntervalHoldAdaptsToStep:
    @pytest.mark.parametrize(
        "step, expected_steps", [(1.0, 5), (0.5, 10), (2.0, 2), (5.0, 1), (10.0, 1)]
    )
    def test_interval_in_steps(self, step, expected_steps):
        strat = IntervalHoldStrategy(RaceConfig(time_step_minutes=step))
        assert strat.interval_steps == expected_steps


class TestCliTimeStep:
    LOCATION = "shenandoah_speedway"

    @staticmethod
    def parse(monkeypatch, *argv):
        monkeypatch.setattr(sys, "argv", ["main.py", *argv])
        return cli.parse_args()

    def test_default_is_one_minute(self, monkeypatch):
        assert self.parse(monkeypatch).time_step_minutes == 1.0

    @pytest.mark.parametrize("raw, value", [("5", 5.0), ("2.5", 2.5), ("0.5", 0.5)])
    def test_flag_parsed(self, monkeypatch, raw, value):
        assert self.parse(monkeypatch, "--time-step-minutes", raw).time_step_minutes == value

    @pytest.mark.parametrize("bad", ["0", "-1", "-0.5", "abc", "inf", "nan", ""])
    def test_invalid_values_rejected_with_usage_error(self, monkeypatch, capsys, bad):
        with pytest.raises(SystemExit) as exc:
            self.parse(monkeypatch, "--time-step-minutes", bad)
        assert exc.value.code == 2
        assert "--time-step-minutes" in capsys.readouterr().err

    @pytest.fixture
    def captured_races(self, monkeypatch):
        races = {"fixed": [], "strategy": [], "single": []}

        def fixed_sweep(**kw):
            races["fixed"].append(kw["base_race"].time_step_minutes)
            return []

        def strategy_sweep(**kw):
            races["strategy"].append(kw["base_race"].time_step_minutes)
            return []

        class FakeSimulator:
            def __init__(self, track, car, race, use_api_weather=True):
                races["single"].append(race.time_step_minutes)

            def run(self):
                return SimpleNamespace()

        class Noop:
            def __init__(self, *a, **k):
                pass

            def print_summary(self):
                pass

        monkeypatch.setattr(cli, "run_fixed_speed_sweep", fixed_sweep)
        monkeypatch.setattr(cli, "run_strategy_sweep", strategy_sweep)
        monkeypatch.setattr(cli, "print_planning_report", lambda **kw: None)
        monkeypatch.setattr(cli, "LapsRaceSimulator", FakeSimulator)
        monkeypatch.setattr(cli, "ResultsReporter", Noop)
        monkeypatch.setattr(cli, "SimulationPlotter", Noop)
        monkeypatch.setattr(
            cli, "save_all_plots", lambda *a, **k: dict(dashboard="", soc="", speed="", weather="")
        )
        monkeypatch.setattr("builtins.input", lambda *a: "")
        return races

    @pytest.mark.parametrize("extra, expected", [([], 1.0), (["--time-step-minutes", "5"], 5.0)])
    def test_single_run_receives_step(self, monkeypatch, captured_races, extra, expected):
        monkeypatch.setattr(sys, "argv", ["main.py", "--location", self.LOCATION, "--strategy", "fixed", *extra])
        cli.main()
        assert captured_races["single"] == [expected]

    @pytest.mark.parametrize("extra, expected", [([], 1.0), (["--time-step-minutes", "5"], 5.0)])
    def test_plan_receives_step(self, monkeypatch, captured_races, extra, expected):
        monkeypatch.setattr(sys, "argv", ["main.py", "--location", self.LOCATION, "--plan", *extra])
        cli.main()
        assert captured_races["fixed"] == [expected]
        assert captured_races["strategy"] == [expected]

    @pytest.mark.parametrize("extra, expected", [([], 1.0), (["--time-step-minutes", "5"], 5.0)])
    def test_speed_sweep_receives_step(self, monkeypatch, captured_races, extra, expected):
        monkeypatch.setattr(sys, "argv", ["main.py", "--location", self.LOCATION, "--speed-sweep", *extra])
        cli.main()
        assert captured_races["fixed"] == [expected]

    def test_end_to_end_offline_run_with_coarse_step(self, monkeypatch, capsys):
        monkeypatch.setattr(cli, "SPEED_SWEEP_MPH", [20])
        monkeypatch.setattr(
            sys, "argv",
            ["main.py", "--location", self.LOCATION, "--speed-sweep", "--time-step-minutes", "5"],
        )
        monkeypatch.setattr(WeatherService, "fetch_weather_data", lambda *a: (_ for _ in ()).throw(ConnectionError("offline")))
        cli.main()
        assert "1 speeds were tested" in capsys.readouterr().out
