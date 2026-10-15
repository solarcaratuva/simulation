from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json
import math
import numpy as np


@dataclass
class TrackConfig:
    name: str
    file_path_name: str
    location: str
    latitude: float
    longitude: float
    lap_distance_m: float
    timezone: str
    total_laps: Optional[int] = None
    elevation: Optional[str] = None
    source: Optional[str] = None

    def __post_init__(self):
        self.validate()

    @property
    def lap_distance_km(self) -> float:
        return self.lap_distance_m / 1000.0

    def validate(self):
        if self.lap_distance_m <= 0:
            raise ValueError("Lap distance must be greater than 0.")
        if self.total_laps is not None and self.total_laps <= 0:
            raise ValueError("Total laps must be greater than 0.")

    @classmethod
    def from_json(cls, filepath: str) -> "TrackConfig":
        with open(filepath, "r") as f:
            course = json.load(f)

        required_fields = (
            "course_name",
            "course_name_argument",
            "lap_distance_m",
            "location",
            "latitude",
            "longitude",
            "timezone",
        )
        missing_fields = [field for field in required_fields if field not in course]
        if missing_fields:
            raise ValueError(
                f"Course file {filepath} is missing required fields: "
                + ", ".join(missing_fields)
            )

        lap_distance_m = course["lap_distance_m"]
        if not isinstance(lap_distance_m, (int, float)) or isinstance(lap_distance_m, bool):
            raise ValueError("lap_distance_m must be a number.")

        return cls(
            name=course["course_name"],
            file_path_name=course["course_name_argument"],
            location=course["location"],
            latitude=course["latitude"],
            longitude=course["longitude"],
            lap_distance_m=float(lap_distance_m),
            timezone=course["timezone"],
            total_laps=course.get("total_laps"),
            elevation=course.get("elevation"),
            source=course.get("source"),
        )


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
        if self.tire_pressure <= 0:
            raise ValueError("Tire pressure must be greater than 0.")
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
    end_time_hour: float = 18.0
    start_soc: float = 1.0
    target_soc: float = 0.10
    min_soc: float = 0.10
    aggressiveness: float = 1.2
    energy_safety_scale: float = 1.0
    initial_speed_mps: float = 20.0
    fixed_speed_mps: float = 15.0
    max_speed_mps: float = 35.0
    min_speed_mps: float = 4.0
    strategy: str = "pi"
    time_step_minutes: float = 1.0

    def __post_init__(self):
        if self.energy_safety_scale >= 1:
            self.energy_safety_scale = 1.0
        elif self.energy_safety_scale <= 0:
            self.energy_safety_scale = 0.01
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
        if self.initial_speed_mps < self.min_speed_mps or self.initial_speed_mps > self.max_speed_mps:
            raise ValueError("Initial speed must be between min and max speed.")
        if self.fixed_speed_mps < self.min_speed_mps or self.fixed_speed_mps > self.max_speed_mps:
            raise ValueError("Fixed speed must be between min and max speed.")


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

def get_available_tracks(courses_dir: Optional[str] = None) -> List[TrackConfig]:
    course_directory = (
        Path(courses_dir)
        if courses_dir is not None
        else Path(__file__).resolve().parents[1] / "courses"
    )
    course_files = sorted(course_directory.glob("*.json"))
    if not course_files:
        raise FileNotFoundError(f"No course JSON files found in {course_directory}")

    return [TrackConfig.from_json(str(course_file)) for course_file in course_files]


def get_track_by_argument(
    course_name_argument: str, courses_dir: Optional[str] = None
) -> TrackConfig:
    tracks = get_available_tracks(courses_dir)
    for track in tracks:
        if track.file_path_name == course_name_argument:
            return track

    available = ", ".join(track.file_path_name for track in tracks)
    raise ValueError(f"Unknown course '{course_name_argument}'. Available courses: {available}")
