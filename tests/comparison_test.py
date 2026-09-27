import unittest
from types import SimpleNamespace

from sim.config import CarConfig, RaceConfig
from sim.planning.comparison import build_comparison_row


class TestComparison(unittest.TestCase):
    def test_battery_energy_calculations(self):
        car = CarConfig(battery_capacity=5000)
        race = RaceConfig(target_soc=0.4)
        results = SimpleNamespace(
            total_laps=1,
            total_distance_miles=1.0,
            final_soc_pct=60.0,
            min_soc_pct=40.0,
            avg_speed_mph=10.0,
            max_speed_mph=12.0,
            min_speed_mph=8.0,
            completed_full_window=True,
            hit_min_soc=False,
        )

        row = build_comparison_row("fixed", race, car, results)

        self.assertAlmostEqual(row["final_battery_energy_wh"], 3000.0) # 5000 * 0.6 = 3000
        self.assertAlmostEqual(row["soc_margin_wh"], 1000.0) # (0.6-0.4) * 5000 = 1000