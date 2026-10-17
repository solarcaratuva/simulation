from sim.config import CarConfig


def build_comparison_row(
    strategy,
    race,
    car: CarConfig,
    results,
    label=None,
    study=None,
    metadata=None,
):
    row = {
        "study": study,
        "label": label or strategy,
        "strategy": strategy,
        "laps": results.total_laps,
        "distance_miles": results.total_distance_miles,
        "final_soc_pct": results.final_soc_pct,
        "min_soc_pct": results.min_soc_pct,
        "target_soc_pct": race.target_soc * 100.0,
        "soc_margin_pct": results.final_soc_pct - (race.target_soc * 100.0),
        "target_battery_energy_wh": car.battery_capacity * race.target_soc,
        "final_battery_energy_wh": car.battery_capacity * results.final_soc_pct / 100.0,
        "energy_margin_wh": (results.final_soc_pct / 100.0 - race.target_soc) * car.battery_capacity,
        "avg_speed_mph": results.avg_speed_mph,
        "max_speed_mph": results.max_speed_mph,
        "min_speed_mph": results.min_speed_mph,
        "completed_full_window": results.completed_full_window,
        "hit_min_soc": results.hit_min_soc,
    }
    if metadata:
        row["metadata"] = metadata
    row["feasibility"] = check_feasibility(row)
    return row

def check_feasibility(row: dict) -> bool:
    return row["completed_full_window"] and row["final_soc_pct"] >= row["target_soc_pct"]


def sort_planning_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["completed_full_window"],
            row["score"]
        ),
        reverse=True,
    )

def score_planning_rows(rows: list[dict]):
    import json
    from pathlib import Path

    with (Path(__file__).parent / "config.json").open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    laps_weight = config["weights"]["laps"]
    minimize_soc_margin_weight = config["weights"]["minimize_soc_margin"]

    realistic_speed = config["realistic_speed"]
    realistic_speed_value = realistic_speed["value"]
    realistic_speed_acceptable_range = realistic_speed["acceptable_range"]
    realistic_speed_penalty = realistic_speed["penalty"]

    strategy_adjustments = {
        strategy: adjustment
        for strategy, adjustment in config["strategy_adjustments"].items()
        if not strategy.startswith("_")
    }

    if not rows:
        return rows

    most_laps = max((row.get("laps", 0) for row in rows), default=0)
    min_realistic_speed = realistic_speed_value - realistic_speed_acceptable_range
    max_realistic_speed = realistic_speed_value + realistic_speed_acceptable_range

    for row in rows:
        # general score calc
        lap_score = row["laps"] / most_laps * 100 if most_laps else 0
        soc_score = 100 - row["soc_margin_pct"]
        score = lap_score * laps_weight + soc_score * minimize_soc_margin_weight

        # penalty for speeds that aren't... that realistic
        avg_speed = row.get("avg_speed_mph")
        if avg_speed is not None and not min_realistic_speed <= avg_speed <= max_realistic_speed:
            score -= realistic_speed_penalty
            row['realistic_speed_penalty'] = True
        else:
            row['realistic_speed_penalty'] = False

        # attempt to get the strategy name, could be under strategy or strategy
        strategy_key = row.get("strategy")
        if strategy_key not in strategy_adjustments:
            strategy_key = row.get("strategy")

        row['strategy_adjustment'] = strategy_adjustments.get(strategy_key, 0)
        score += strategy_adjustments.get(strategy_key, 0)
        row["score"] = score
    return rows

