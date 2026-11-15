# tests/test_config.py

import pytest
from sim.config import CarConfig, RaceConfig, TrackConfig

def test_invalid_car_config():
    with pytest.raises(ValueError, match="Battery capacity must be greater than 0."):
        CarConfig(battery_capacity_wh=0, mass_kg=1000, solar_panel_area_m2=1, solar_panel_efficiency=0.2, electrical_efficiency=0.9, regen_efficiency=0.8)

    with pytest.raises(ValueError, match="Mass must be greater than 0."):
        CarConfig(battery_capacity_wh=50, mass_kg=0, solar_panel_area_m2=1, solar_panel_efficiency=0.2, electrical_efficiency=0.9, regen_efficiency=0.8)

    with pytest.raises(ValueError, match="Tire pressure must be greater than 0."):
        CarConfig(tire_pressure_bar=0)

def test_invalid_race_config():
    with pytest.raises(ValueError, match="Start SOC must be between 0 and 1."):
        RaceConfig(start_soc=1.5, target_soc=0.8, min_soc=0.2, max_speed_mps=30, min_speed_mps=10, time_step_minutes=1)

    with pytest.raises(ValueError, match="SOC values must satisfy: min_soc <= target_soc <= start_soc."):
        RaceConfig(start_soc=0.5, target_soc=0.6, min_soc=0.7, max_speed_mps=30, min_speed_mps=10, time_step_minutes=1)

def test_energy_safety_scale_preserves_clamping():
    assert RaceConfig(energy_safety_scale=2).energy_safety_scale == 1.0
    assert RaceConfig(energy_safety_scale=0).energy_safety_scale == 0.01

def test_invalid_track_config():
    with pytest.raises(ValueError, match="Lap distance must be greater than 0."):
        TrackConfig(
            name="test",
            file_path_name="test",
            location="test",
            latitude=0,
            longitude=0,
            lap_distance_m=0,
            timezone="UTC",
        )


def test_from_json_accepts_legacy_names(tmp_path):
    import json
    legacy = {"mass": 300, "battery_capacity": 4000, "solar_panel_area": 3,
              "C_dA": 0.5, "rho": 1.1, "tire_pressure": 4}
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(legacy))
    car = CarConfig.from_json(str(path))
    assert car.mass_kg == 300
    assert car.battery_capacity_wh == 4000
    assert car.solar_panel_area_m2 == 3
    assert car.cda_m2 == 0.5
    assert car.air_density_kg_per_m3 == 1.1
    assert car.tire_pressure_bar == 4
