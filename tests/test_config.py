# tests/test_config.py

import pytest
from sim.config import CarConfig, RaceConfig, TrackConfig

def test_invalid_car_config():
    with pytest.raises(ValueError, match="Battery capacity must be greater than 0."):
        CarConfig(battery_capacity=0, mass=1000, solar_panel_area=1, solar_panel_efficiency=0.2, electrical_efficiency=0.9, regen_efficiency=0.8)

    with pytest.raises(ValueError, match="Mass must be greater than 0."):
        CarConfig(battery_capacity=50, mass=0, solar_panel_area=1, solar_panel_efficiency=0.2, electrical_efficiency=0.9, regen_efficiency=0.8)

def test_invalid_race_config():
    with pytest.raises(ValueError, match="Start SOC must be between 0 and 1."):
        RaceConfig(start_soc=1.5, target_soc=0.8, min_soc=0.2, max_speed_mps=30, min_speed_mps=10, time_step_minutes=1)

    with pytest.raises(ValueError, match="SOC values must satisfy: min_soc <= target_soc <= start_soc."):
        RaceConfig(start_soc=0.5, target_soc=0.6, min_soc=0.7, max_speed_mps=30, min_speed_mps=10, time_step_minutes=1)

def test_invalid_track_config():
    with pytest.raises(ValueError, match="Lap distance must be greater than 0."):
        TrackConfig(lap_distance_km=0)