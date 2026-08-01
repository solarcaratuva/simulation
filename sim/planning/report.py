from sim.planning.comparison import sort_planning_rows


def print_planning_report(
    *,
    track,
    fixed_speed_rows: list[dict],
    strategy_rows: list[dict],
) -> None:
    combined_rows = fixed_speed_rows + strategy_rows
    best_fixed_speed_row = (
        sort_planning_rows(fixed_speed_rows)[0]
        if fixed_speed_rows
        else None
    )
    best_row = (
        sort_planning_rows(combined_rows)[0]
        if combined_rows
        else None
    )

    print("PRE-RACE PLANNING REPORT")
    print()
    print(f"Track: {track.name}")
    print(f"Location: {track.location}")
    print()

    print("Best Fixed Speed:")
    if best_fixed_speed_row is None:
        print("  No fixed-speed rows provided.")
    else:
        print(f"  {best_fixed_speed_row['label']}")
        print(f"  Laps: {best_fixed_speed_row['laps']}")
        print(f"  Final SoC: {best_fixed_speed_row['final_soc_pct']:.1f}%")
        print(f"  Avg Speed: {best_fixed_speed_row['avg_speed_mph']:.1f} mph")
    print()

    print("Strategy Comparison:")
    if not strategy_rows:
        print("  No strategy rows provided.")
    for row in strategy_rows:
        status = (
            "hit minimum SoC early"
            if row["hit_min_soc"]
            else "full race"
        )
        print(
            f"  {row['strategy']:<14}"
            f" {row['laps']:>3} laps"
            f"  {row['final_soc_pct']:>5.1f}% final SoC"
            f"  {status}"
        )
    print()

    print("Recommendation:")
    if best_row is None:
        print("  No planning rows provided.")
    else:
        print(f"  Use {best_row['label']}.")
        print(
            f"  Expected result: {best_row['laps']} laps, "
            f"{best_row['final_soc_pct']:.1f}% final SoC."
        )
