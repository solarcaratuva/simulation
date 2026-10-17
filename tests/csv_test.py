import csv
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sim.config import CarConfig, TrackConfig
from sim.main import main as run_main, run_speed_sweep


class TestCSV(unittest.TestCase):
    def test_fixed_speed_sweep(self):
        car = CarConfig()
        track = TrackConfig(
            name="Test Track",
            file_path_name="test_track",
            location="Test Location",
            latitude=0.0,
            longitude=0.0,
            lap_distance_km=1.0,
            timezone="UTC",
        )
        simulator_args = []

        class StubSimulator:
            def __init__(self, *, track, car, race, use_api_weather):
                simulator_args.append((track, car, use_api_weather))

            def run(self):
                return SimpleNamespace(
                    total_laps=1,
                    total_distance_miles=1.0,
                    final_soc_pct=80.0,
                    min_soc_pct=75.0,
                    avg_speed_mph=20.0,
                    max_speed_mph=20.0,
                    min_speed_mph=20.0,
                    completed_full_window=True,
                    hit_min_soc=False,
                    reached_min_soc_time_minutes=480.0,
                )

        with tempfile.TemporaryDirectory() as output_dir:
            with patch("sim.planning.sweep.LapsRaceSimulator", StubSimulator):
                with patch("sim.main.os.getcwd", return_value=output_dir):
                    run_speed_sweep(track, car, None)

            csv_path = os.path.join(output_dir, "csv", "planning_report.csv")
            self.assertTrue(os.path.isfile(csv_path))

            with open(csv_path, newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))

        csv_columns = rows[0].keys()
        self.assertIn("study", csv_columns)
        self.assertIn("label", csv_columns)
        self.assertIn("strategy", csv_columns)
        self.assertIn("mph", csv_columns)
        self.assertIn("laps", csv_columns)
        self.assertIn("distance_miles", csv_columns)
        self.assertIn("final_soc_pct", csv_columns)
        self.assertIn("target_soc_pct", csv_columns)
        self.assertIn("soc_margin_pct", csv_columns)
        self.assertIn("energy_margin_wh", csv_columns)
        self.assertIn("feasibility", csv_columns)
        self.assertIn("avg_speed_mph", csv_columns)
        self.assertTrue(len(rows) > 1)

    def test_planning_report(self):
        car = CarConfig()
        track = TrackConfig(
            name="Test Track",
            file_path_name="test_track",
            location="Test Location",
            latitude=0.0,
            longitude=0.0,
            lap_distance_km=1.0,
            timezone="UTC",
        )

        class StubSimulator:
            def __init__(self, *, track, car, race, use_api_weather):
                pass

            def run(self):
                return SimpleNamespace(
                    total_laps=1,
                    total_distance_miles=1.0,
                    final_soc_pct=80.0,
                    min_soc_pct=75.0,
                    avg_speed_mph=20.0,
                    max_speed_mph=20.0,
                    min_speed_mph=20.0,
                    completed_full_window=True,
                    hit_min_soc=False,
                    reached_min_soc_time_minutes=480.0,
                )

        args = SimpleNamespace(
            plan=True,
            speed_sweep=False,
            location=track.file_path_name,
        )
        with tempfile.TemporaryDirectory() as output_dir:
            with patch("sim.main.parse_args", return_value=args):
                with patch("sim.main.get_available_tracks", return_value=[track]):
                    with patch("sim.main.CarConfig.from_json", return_value=car):
                        with patch("sim.planning.sweep.LapsRaceSimulator", StubSimulator):
                            with patch("sim.main.os.getcwd", return_value=output_dir):
                                run_main()

            csv_path = os.path.join(output_dir, "csv", "planning_report.csv")
            self.assertTrue(os.path.isfile(csv_path))

            with open(csv_path, newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))

        csv_columns = rows[0].keys()
        self.assertIn("study", csv_columns)
        self.assertIn("label", csv_columns)
        self.assertIn("strategy", csv_columns)
        self.assertIn("mph", csv_columns)
        self.assertIn("laps", csv_columns)
        self.assertIn("distance_miles", csv_columns)
        self.assertIn("final_soc_pct", csv_columns)
        self.assertIn("target_soc_pct", csv_columns)
        self.assertIn("soc_margin_pct", csv_columns)
        self.assertIn("energy_margin_wh", csv_columns)
        self.assertIn("feasibility", csv_columns)
        self.assertIn("avg_speed_mph", csv_columns)
        self.assertTrue(len(rows) > 1)