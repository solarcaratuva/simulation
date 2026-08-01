def build_comparison_row(strategy, race, results, label=None, study=None):
    return {
        "study": study,
        "label": label or strategy,
        "strategy": strategy,
        "laps": results.total_laps,
        "distance_miles": results.total_distance_miles,
        "final_soc_pct": results.final_soc_pct,
        "min_soc_pct": results.min_soc_pct,
        "target_soc_pct": race.target_soc * 100.0,
        "avg_speed_mph": results.avg_speed_mph,
        "max_speed_mph": results.max_speed_mph,
        "min_speed_mph": results.min_speed_mph,
        "completed_full_window": results.completed_full_window,
        "hit_min_soc": results.hit_min_soc,
    }

def sort_planning_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row["completed_full_window"],
            row["laps"],
            row["final_soc_pct"],
        ),
        reverse=True,
    )