"""Tests for the --no-api-weather CLI flag (offline mode)."""
import sys
from types import SimpleNamespace

import pytest

from sim import main as cli
from sim.weather import WeatherService

LOCATION = "shenandoah_speedway"


def run_cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["main.py", *argv])
    cli.main()


@pytest.fixture
def recorded(monkeypatch):
    """Replace the heavy sim entry points in sim.main and record use_api_weather."""
    calls = {"fixed": [], "strategy": [], "simulator": []}

    def fake_fixed_sweep(**kwargs):
        calls["fixed"].append(kwargs["use_api_weather"])
        return []

    def fake_strategy_sweep(**kwargs):
        calls["strategy"].append(kwargs["use_api_weather"])
        return []

    class FakeSimulator:
        def __init__(self, track, car, race, use_api_weather=True):
            calls["simulator"].append(use_api_weather)

        def run(self):
            return SimpleNamespace()

    class FakeReporter:
        def __init__(self, *args, **kwargs):
            pass

        def print_summary(self):
            pass

    monkeypatch.setattr(cli, "run_fixed_speed_sweep", fake_fixed_sweep)
    monkeypatch.setattr(cli, "run_strategy_sweep", fake_strategy_sweep)
    monkeypatch.setattr(cli, "print_planning_report", lambda **kwargs: None)
    monkeypatch.setattr(cli, "LapsRaceSimulator", FakeSimulator)
    monkeypatch.setattr(cli, "ResultsReporter", FakeReporter)
    monkeypatch.setattr(cli, "SimulationPlotter", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "save_all_plots",
        lambda *a, **k: {"dashboard": "", "soc": "", "speed": "", "weather": ""},
    )
    monkeypatch.setattr("builtins.input", lambda *a: "")  # accept default safety scale
    return calls


class TestParseArgs:
    def test_defaults_to_api_weather(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["main.py"])
        assert cli.parse_args().no_api_weather is False

    def test_flag_enables_offline_mode(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["main.py", "--no-api-weather"])
        assert cli.parse_args().no_api_weather is True

    def test_flag_combines_with_other_modes(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["main.py", "--plan", "--no-api-weather"])
        args = cli.parse_args()
        assert args.plan is True and args.no_api_weather is True


@pytest.mark.parametrize(
    "extra, expected_use_api",
    [([], True), (["--no-api-weather"], False)],
    ids=["default-uses-api", "flag-goes-offline"],
)
class TestFlagIsPassedThrough:
    def test_single_run(self, monkeypatch, recorded, extra, expected_use_api):
        run_cli(monkeypatch, "--location", LOCATION, "--strategy", "fixed", *extra)
        assert recorded["simulator"] == [expected_use_api]

    def test_plan_mode(self, monkeypatch, recorded, extra, expected_use_api):
        run_cli(monkeypatch, "--location", LOCATION, "--plan", *extra)
        assert recorded["fixed"] == [expected_use_api]
        assert recorded["strategy"] == [expected_use_api]

    def test_speed_sweep_mode(self, monkeypatch, recorded, extra, expected_use_api):
        run_cli(monkeypatch, "--location", LOCATION, "--speed-sweep", *extra)
        assert recorded["fixed"] == [expected_use_api]


class TestRealWeatherPath:
    """Run the real simulator (small sweep) and watch the weather API boundary."""

    @pytest.fixture(autouse=True)
    def small_sweep(self, monkeypatch):
        monkeypatch.setattr(cli, "SPEED_SWEEP_MPH", [20])

    def test_offline_mode_never_calls_the_api(self, monkeypatch, capsys):
        def fail(self, race):
            raise AssertionError("weather API was called in offline mode")

        monkeypatch.setattr(WeatherService, "fetch_weather_data", fail)
        run_cli(monkeypatch, "--location", LOCATION, "--speed-sweep", "--no-api-weather")

        out = capsys.readouterr().out
        assert "1 speeds were tested" in out
        assert "API fetch failed" not in out

    def test_default_tries_api_then_falls_back_to_synthetic(self, monkeypatch, capsys):
        attempts = []

        def unreachable(self, race):
            attempts.append(race)
            raise ConnectionError("no network")

        monkeypatch.setattr(WeatherService, "fetch_weather_data", unreachable)
        run_cli(monkeypatch, "--location", LOCATION, "--speed-sweep")

        out = capsys.readouterr().out
        assert attempts, "default mode should attempt the API first"
        assert "API fetch failed" in out
        assert "1 speeds were tested" in out
