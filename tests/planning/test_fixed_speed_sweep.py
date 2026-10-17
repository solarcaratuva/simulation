import unittest
from contextlib import redirect_stdout
from io import StringIO

from sim.main import print_speed_sweep_summary


class TestFixedSpeedSweepSummary(unittest.TestCase):
    def get_summary(self, rows):
        output = StringIO()
        with redirect_stdout(output):
            print_speed_sweep_summary(rows)
        return output.getvalue()

    def test_no_speeds_are_feasible(self):
        rows = [
            {"mph": 20, "feasibility": False, "distance_miles": 120},
            {"mph": 30, "feasibility": False, "distance_miles": 150},
        ]

        summary = self.get_summary(rows)

        self.assertIn("2 speeds were tested", summary)
        self.assertIn("No speeds were feasible!", summary)
        self.assertNotIn("Slowest feasible speed:", summary)
        self.assertNotIn("Best feasible fixed speed", summary)

    def test_some_speeds_are_feasible(self):
        rows = [
            {"mph": 20, "feasibility": True, "distance_miles": 100},
            {"mph": 30, "feasibility": False, "distance_miles": 150},
            {"mph": 40, "feasibility": True, "distance_miles": 180},
        ]

        summary = self.get_summary(rows)

        self.assertIn("3 speeds were tested", summary)
        self.assertIn("Slowest feasible speed: 20 mph", summary)
        self.assertIn("Fastest feasible speed: 40 mph", summary)
        self.assertIn("Best feasible fixed speed (max distance): 40 mph with 180.0 mi", summary)
        self.assertNotIn("All speeds were feasible!", summary)

    def test_all_speeds_are_feasible(self):
        rows = [
            {"mph": 20, "feasibility": True, "distance_miles": 100},
            {"mph": 30, "feasibility": True, "distance_miles": 200},
            {"mph": 40, "feasibility": True, "distance_miles": 180},
        ]

        summary = self.get_summary(rows)

        self.assertIn("3 speeds were tested", summary)
        self.assertIn("Slowest feasible speed: 20 mph", summary)
        self.assertIn("Fastest feasible speed: 40 mph", summary)
        self.assertIn("Best feasible fixed speed (max distance): 30 mph with 200.0 mi", summary)
        self.assertIn("All speeds were feasible!", summary)


if __name__ == "__main__":
    unittest.main()