import argparse
from dataclasses import asdict
from pathlib import Path
import sys
from typing import Union

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.config import SimulationResults
from sim.planning.sweep import (
    run_fixed_speed_sweep,
    run_strategy_sweep,
)
from sim.plotting import SimulationPlotter, save_all_plots
from sim.reporting import ResultsReporter
from sim.loader import LoadedScenario, load_scenario
from sim.simulator import LapsRaceSimulator


LoadedPlanningResults = tuple[list[dict], list[dict]]
ScenarioResults = Union[SimulationResults, LoadedPlanningResults]


def run_loaded_scenario(scenario: LoadedScenario) -> SimulationResults:
    if not scenario.use_api_weather:
        np.random.seed(scenario.synthetic_weather_seed)

    simulator = LapsRaceSimulator(
        track=scenario.track,
        car=scenario.car,
        race=scenario.race,
        use_api_weather=scenario.use_api_weather,
    )
    return simulator.run()


def run_loaded_planning(scenario: LoadedScenario) -> LoadedPlanningResults:
    fixed_speed_rows = run_fixed_speed_sweep(
        track=scenario.track,
        car=scenario.car,
        base_race=scenario.race,
        speeds_mph=scenario.fixed_speed_values_mph,
        use_api_weather=scenario.use_api_weather,
        synthetic_weather_seed=scenario.synthetic_weather_seed,
    )
    aggressiveness_by_strategy = {
        "pi": 1.5,
        "stepped": 1.2,
        "interval-hold": 1.0,
        "fixed": 1.0,
    }
    strategy_rows = run_strategy_sweep(
        track=scenario.track,
        car=scenario.car,
        base_race=scenario.race,
        strategies=scenario.strategies,
        aggressiveness_by_strategy=aggressiveness_by_strategy,
        use_api_weather=scenario.use_api_weather,
        synthetic_weather_seed=scenario.synthetic_weather_seed,
    )
    return fixed_speed_rows, strategy_rows


def run_scenario_file(scenario_path: str | Path) -> ScenarioResults:
    scenario = load_scenario(scenario_path)
    if scenario.planning_enabled:
        return run_loaded_planning(scenario)
    return run_loaded_scenario(scenario)


def print_scenario_parameters(scenario: LoadedScenario) -> None:
    print("\nScenario Parameters")
    print("=" * 80)
    print(f"  Name: {scenario.name}")
    print(f"  Course: {scenario.track.name}")
    print(f"  Location: {scenario.track.location}")
    print(f"  Weather: {'api' if scenario.use_api_weather else 'synthetic'}")
    if not scenario.use_api_weather:
        print(f"  Synthetic weather seed: {scenario.synthetic_weather_seed}")

    print("\n  Race:")
    for key, value in asdict(scenario.race).items():
        print(f"    {key}: {value}")

    print("\n  Car:")
    for key, value in asdict(scenario.car).items():
        print(f"    {key}: {value}")

    if scenario.planning_enabled:
        print("\n  Planning:")
        print(f"    strategies: {', '.join(scenario.strategies)}")
        print(f"    fixed_speed_values_mph: {scenario.fixed_speed_values_mph}")
    print("=" * 80)


def report_single_run(scenario: LoadedScenario, results: SimulationResults) -> None:
    print("\nStarting Scenario Simulation")
    print(f"  Scenario: {scenario.name}")
    print(f"  Track: {scenario.track.name}")
    print(f"  Location: {scenario.track.location}")
    print(f"  Strategy: {scenario.race.strategy}")
    print(f"  Aggressiveness: {scenario.race.aggressiveness:.2f}")

    reporter = ResultsReporter(results, scenario.track, scenario.race)
    reporter.print_summary()

    output_dir = "plots/laps_modular"
    prefix = f"{scenario.track.file_path_name}_{scenario.race.strategy}"
    plotter = SimulationPlotter(results, scenario.track)
    saved = save_all_plots(plotter, output_dir, prefix)

    print("Saved plots:")
    for plot_path in saved.values():
        print(f"  - {plot_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simulation from a YAML scenario")
    parser.add_argument("--scenario", required=True, type=Path)
    args = parser.parse_args()
    scenario = load_scenario(args.scenario)
    print_scenario_parameters(scenario)

    result = (
        run_loaded_planning(scenario)
        if scenario.planning_enabled
        else run_loaded_scenario(scenario)
    )
    if isinstance(result, tuple):
        fixed_rows, strategy_rows = result
        print(f"Completed planning scenario: {len(fixed_rows)} fixed-speed rows, "
              f"{len(strategy_rows)} strategy rows")
    else:
        report_single_run(scenario, result)


if __name__ == "__main__":
    main()
