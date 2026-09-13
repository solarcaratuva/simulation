from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import math
import numpy as np


@dataclass
class TrackConfig:
    name: str
    location: str
    latitude: float
    longitude: float
    lap_distance_km: float
    timezone: str
    lap_distance_m: float = field(init=False)

    def __post_init__(self):
        self.lap_distance_m = self.lap_distance_km * 1000.0
        self.validate()

    def validate(self):
        if self.lap_distance_km <= 0:
            raise ValueError("Lap distance must be greater than 0.")


@dataclass
class CarConfig:
    mass: float = 337
    battery_capacity: float = 5000
    solar_panel_area: float = 4
    solar_panel_efficiency: float = 0.23
    electrical_efficiency: float = 0.99
    C_dA: float = 0.73809
    tire_pressure: float = 5
    regen_efficiency: float = 0.5
    rho: float = 1.192
    g: float = 9.80665

    def __post_init__(self):
        self.validate()

    def validate(self):
        if self.mass <= 0:
            raise ValueError("Mass must be greater than 0.")
        if self.battery_capacity <= 0:
            raise ValueError("Battery capacity must be greater than 0.")
        if self.solar_panel_area < 0:
            raise ValueError("Solar panel area must be non-negative.")
        if not (0 <= self.solar_panel_efficiency <= 1):
            raise ValueError("Solar panel efficiency must be between 0 and 1.")
        if not (0 <= self.electrical_efficiency <= 1):
            raise ValueError("Electrical efficiency must be between 0 and 1.")
        if not (0 <= self.regen_efficiency <= 1):
            raise ValueError("Regen efficiency must be between 0 and 1.")

    @classmethod
    def from_json(cls, filepath: str) -> "CarConfig":
        with open(filepath, "r") as f:
            params = json.load(f)

        for key, value in params.items():
            if value == "inf":
                params[key] = math.inf

        return cls(
            mass=params.get("mass", 337),
            battery_capacity=params.get("battery_capacity", 5000),
            solar_panel_area=params.get("solar_panel_area", 4),
            solar_panel_efficiency=params.get("solar_panel_efficiency", 0.23),
            electrical_efficiency=params.get("electrical_efficiency", 0.99),
            C_dA=params.get("C_dA", 0.73809),
            tire_pressure=params.get("tire_pressure", 5),
            regen_efficiency=params.get("regen_efficiency", 0.5),
            rho=params.get("rho", 1.192),
            g=params.get("g", 9.80665),
        )


@dataclass
class RaceConfig:
    start_time_hour: float = 10.0
    start_soc: float = 1.0
    target_soc: float = 0.8
    min_soc: float = 0.2
    max_speed_mps: float = 30.0
    min_speed_mps: float = 10.0
    time_step_minutes: float = 1.0

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not (0 <= self.start_soc <= 1):
            raise ValueError("Start SOC must be between 0 and 1.")
        if not (0 <= self.target_soc <= 1):
            raise ValueError("Target SOC must be between 0 and 1.")
        if not (0 <= self.min_soc <= 1):
            raise ValueError("Min SOC must be between 0 and 1.")
        if not (self.min_soc <= self.target_soc <= self.start_soc):
            raise ValueError("SOC values must satisfy: min_soc <= target_soc <= start_soc.")
        if self.max_speed_mps <= self.min_speed_mps:
            raise ValueError("Max speed must be greater than min speed.")
        if self.time_step_minutes <= 0:
            raise ValueError("Time step must be greater than 0.")


@dataclass
class SimulationResults:
    time_minutes: np.ndarray
    soc: np.ndarray
    speed: np.ndarray
    ghi: np.ndarray
    cloud_cover: np.ndarray
    lap_times: List[float]
    total_laps: int
    total_distance_m: float
    bdr: np.ndarray
    ideal_soc: np.ndarray
    completed_full_window: bool
    reached_min_soc_time_minutes: Optional[float]
    laps_at_min_soc: Optional[int]

    @property
    def total_distance_km(self) -> float:
        return self.total_distance_m / 1000.0

    @property
    def total_distance_miles(self) -> float:
        return self.total_distance_m / 1609.34

    @property
    def avg_speed_mps(self) -> float:
        return float(np.mean(self.speed))

    @property
    def avg_speed_mph(self) -> float:
        return self.avg_speed_mps * 2.237

    @property
    def final_soc(self) -> float:
        return float(self.soc[-1])
    
    @property
    def final_soc_pct(self) -> float:
        return self.final_soc * 100.0

    @property
    def min_soc(self) -> float:
        return float(np.min(self.soc))

    @property
    def min_soc_pct(self) -> float:
        return self.min_soc * 100.0

    @property
    def hit_min_soc(self) -> bool:
        return not self.completed_full_window

    @property
    def max_speed_mph(self) -> float:
        return float(np.max(self.speed)) * 2.237

    @property
    def min_speed_mph(self) -> float:
        return float(np.min(self.speed)) * 2.237

def get_available_tracks() -> List[TrackConfig]:
    return [
        TrackConfig(
            name="Shenandoah Speedway",
            location="Page County, Virginia",
            latitude=38.5110,
            longitude=-78.6359,
            lap_distance_km=0.604,
            timezone="America/New_York",
        ),
        TrackConfig(
            name= "Virginia International Raceway (Patriot Course)",
            location="Alton, Virginia",
            latitude=36.5666,
            longitude=-79.2058,
            lap_distance_km=1.77,
            timezone="America/New_York"
        ),
        TrackConfig(
            name= "Brainerd International Raceway (Donnybrooke Course)",
            location="Brainerd, Minnesota",
            latitude=46.4176,
            longitude=-94.2853,
            lap_distance_km=4.989,
            timezone="America/Chicago"
        )
    ]
