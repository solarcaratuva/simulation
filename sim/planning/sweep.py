from dataclasses import replace

import numpy as np

from sim.planning.comparison import build_comparison_row
from sim.simulator import LapsRaceSimulator


MPH_TO_MPS = 1 / 2.237
SPEED_SWEEP_MPH = list(range(10, 47, 2))

DEFAULT_AGGRESSIVENESS = {
    "pi": 1.5,
    "stepped": 1.2,
    "interval-hold": 1.0,
    "fixed": 1.0,
}


def run_fixed_speed_sweep(
    *,
    track,
    car,
    base_race,
    speeds_mph: list[int],
    use_api_weather: bool = True,
    synthetic_weather_seed: int = 7,
) -> list[dict]:
    rows = []

    for mph in speeds_mph:
        fixed_speed_mps = mph * MPH_TO_MPS
        race = replace(
            base_race,
            strategy="fixed",
            fixed_speed_mps=fixed_speed_mps,
        )

        simulator = LapsRaceSimulator(
            track=track,
            car=car,
            race=race,
            use_api_weather=use_api_weather,
        )
        np.random.seed(synthetic_weather_seed)
        results = simulator.run()

        row = build_comparison_row(
            "fixed",
            race,
            results,
            label=f"{mph} mph",
            study="fixed-speed",
        )
        row["mph"] = mph
        row["fixed_speed_mps"] = fixed_speed_mps
        row["reached_min_soc_time_minutes"] = results.reached_min_soc_time_minutes
        rows.append(row)

    return rows


def run_strategy_sweep(
    *,
    track,
    car,
    base_race,
    strategies: list[str],
    aggressiveness_by_strategy: dict[str, float],
    use_api_weather: bool = True,
    synthetic_weather_seed: int = 7,
) -> list[dict]:
    rows = []

    for strategy in strategies:
        race = replace(
            base_race,
            strategy=strategy,
            aggressiveness=aggressiveness_by_strategy[strategy],
        )

        simulator = LapsRaceSimulator(
            track=track,
            car=car,
            race=race,
            use_api_weather=use_api_weather,
        )
        np.random.seed(synthetic_weather_seed)
        results = simulator.run()
        rows.append(build_comparison_row(strategy, race, results, study="strategy"))

    return rows
