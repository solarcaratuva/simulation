import unittest

from sim.planning.comparison import check_feasibility


class TestFeasibility(unittest.TestCase):

    def test_feasible(self):
        row = {
            "final_soc_pct": 50.0,
            "target_soc_pct": 40.0,
            "completed_full_window": True,
        }

        self.assertTrue(check_feasibility(row))

    def test_infeasible_low_soc(self):
        row = {
            "final_soc_pct": 30.0,
            "target_soc_pct": 40.0,
            "completed_full_window": True,
        }

        self.assertFalse(check_feasibility(row))

    def test_infeasible_not_completed(self):
        row = {
            "final_soc_pct": 50.0,
            "target_soc_pct": 40.0,
            "completed_full_window": False,
        }

        self.assertFalse(check_feasibility(row))

    def test_feasible_equal_soc(self):
        row = {
            "final_soc_pct": 40.0,
            "target_soc_pct": 40.0,
            "completed_full_window": True,
        }

        self.assertTrue(check_feasibility(row))
