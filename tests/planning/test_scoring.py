import unittest

from sim.planning.comparison import score_planning_rows, sort_planning_rows


class TestScoring(unittest.TestCase):
    def test_feasible_over_infeasible(self):
        rows = [
            {
                "completed_full_window": True,
                "final_soc_pct": 50,
                "target_soc_pct": 40,
                "feasibility": True,
                "score": 50,
            },
            {
                "completed_full_window": False,
                "final_soc_pct": 90,
                "target_soc_pct": 40,
                "feasibility": False,
                "score": 100,
            },
        ]

        sorted_rows = sort_planning_rows(rows)
        self.assertTrue(sorted_rows[0]["feasibility"])

    def test_calculations(self):
        config = {
            "weights": {"laps": 0.7, "minimize_soc_margin": 0.3},
            "realistic_speed": {
                "value": 25,
                "acceptable_range": 5,
                "penalty": 15,
            },
            "strategy_adjustments": {"stepped": 10, "pi": -5},
        }
        rows = [
            {
                "laps": 10,
                "soc_margin_pct": 20,
                "strategy": "stepped",
            },
            {
                "laps": 8,
                "soc_margin_pct": 10,
                "strategy": "pi",
            },
            {
                "laps": 5,
                "soc_margin_pct": 30,
                "avg_speed_mph": 10,
                "strategy": "fixed"
            }
        ]

        score_planning_rows(rows, config)

        self.assertEqual(rows[0]["score"], 104)
        self.assertEqual(rows[0]["realistic_speed_penalty"], False)
        self.assertEqual(rows[1]["score"], 78)
        self.assertEqual(rows[1]["realistic_speed_penalty"], False)
        self.assertEqual(rows[2]["score"], 41)
        self.assertEqual(rows[2]["realistic_speed_penalty"], True)
