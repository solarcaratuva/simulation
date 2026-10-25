from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sim.config import CarConfig, RaceConfig, TrackConfig


SUPPORTED_STRATEGIES = ("pi", "stepped", "interval-hold", "fixed")
DEFAULT_STRATEGIES = list(SUPPORTED_STRATEGIES)
DEFAULT_FIXED_SPEED_VALUES_MPH = list(range(10, 47, 2))


@dataclass(frozen=True)
class PlanningConfig:
    enabled: bool = False
    strategies: list[str] | None = None
    fixed_speed_values_mph: list[int] | None = None

    def __post_init__(self) -> None:
        if self.strategies is None:
            object.__setattr__(self, "strategies", list(DEFAULT_STRATEGIES))
        if self.fixed_speed_values_mph is None:
            object.__setattr__(
                self,
                "fixed_speed_values_mph",
                list(DEFAULT_FIXED_SPEED_VALUES_MPH),
            )


@dataclass(frozen=True)
class LoadedScenario:
    name: str
    car: CarConfig
    track: TrackConfig
    race: RaceConfig
    use_api_weather: bool
    synthetic_weather_seed: int
    planning: PlanningConfig

    @property
    def planning_enabled(self) -> bool:
        return self.planning.enabled

    @property
    def strategies(self) -> list[str]:
        return self.planning.strategies or []

    @property
    def fixed_speed_values_mph(self) -> list[int]:
        return self.planning.fixed_speed_values_mph or []


class ScenarioLoader:
    def __init__(
        self,
        scenario_path: str | Path,
        repo_root: str | Path | None = None,
    ) -> None:
        self.scenario_path = Path(scenario_path).expanduser().resolve()
        self.repo_root = (
            Path(repo_root).expanduser().resolve()
            if repo_root is not None
            else Path(__file__).resolve().parents[1]
        )

    def load(self) -> LoadedScenario:
        values = self._read_yaml()
        scenario = self._mapping(values, "scenario")

        name = self._required_string(scenario, "name")
        car_reference = self._required_string(scenario, "car_parameter_file")
        course_reference = self._required_string(scenario, "course_file")

        car = self._load_car(self._resolve_reference(car_reference, "car_parameter_file"))
        track = self._load_course(self._resolve_reference(course_reference, "course_file"))

        race_values = self._mapping(scenario, "race")
        strategy_values = self._mapping(scenario, "strategy")
        simulation_values = self._mapping(scenario, "simulation", required=False)
        weather_values = self._mapping(scenario, "weather")

        race = self._build_race_config(
            race_values,
            strategy_values,
            simulation_values,
        )
        use_api_weather, synthetic_weather_seed = self._build_weather_config(weather_values)
        planning = self._build_planning_config(scenario)

        return LoadedScenario(
            name=name,
            car=car,
            track=track,
            race=race,
            use_api_weather=use_api_weather,
            synthetic_weather_seed=synthetic_weather_seed,
            planning=planning,
        )

    def _read_yaml(self) -> dict[str, Any]:
        if not self.scenario_path.is_file():
            raise FileNotFoundError(f"Scenario file not found: {self.scenario_path}")

        try:
            with self.scenario_path.open("r", encoding="utf-8") as scenario_file:
                values = yaml.safe_load(scenario_file)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in scenario file {self.scenario_path}: {exc}") from exc

        if not isinstance(values, dict):
            raise ValueError("Scenario file must contain a mapping at the top level")
        if "scenario" not in values:
            raise ValueError("Scenario file is missing required top-level 'scenario' section")
        return values

    def _resolve_reference(self, reference: str, field_name: str) -> Path:
        reference_path = Path(reference).expanduser()
        candidates = [
            reference_path
            if reference_path.is_absolute()
            else self.scenario_path.parent / reference_path,
            self.repo_root / reference_path,
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file():
                return resolved
        raise FileNotFoundError(
            f"Referenced {field_name} file not found: {reference}"
        )

    def _load_car(self, path: Path) -> CarConfig:
        return CarConfig.from_json(str(path))

    def _load_course(self, path: Path) -> TrackConfig:
        return TrackConfig.from_json(str(path))

    def _build_race_config(
        self,
        race_values: dict[str, Any],
        strategy_values: dict[str, Any],
        simulation_values: dict[str, Any],
    ) -> RaceConfig:
        values: dict[str, Any] = dict(race_values)
        values["strategy"] = self._required_string(strategy_values, "name")
        values.update(
            {
                key: value
                for key, value in strategy_values.items()
                if key != "name"
            }
        )
        values.update(simulation_values)

        if values["strategy"] not in SUPPORTED_STRATEGIES:
            raise ValueError(
                f"Unsupported strategy '{values['strategy']}'. "
                f"Expected one of: {', '.join(SUPPORTED_STRATEGIES)}"
            )
        return RaceConfig(**values)

    def _build_weather_config(self, values: dict[str, Any]) -> tuple[bool, int]:
        source = self._required_string(values, "source")
        if source not in ("api", "synthetic"):
            raise ValueError("Weather source must be 'api' or 'synthetic'")

        seed = values.get("random_seed", 7)
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("weather.random_seed must be an integer")
        return source == "api", seed

    def _build_planning_config(self, scenario: dict[str, Any]) -> PlanningConfig:
        planning_values = scenario.get("planning", {})
        if not isinstance(planning_values, dict):
            raise ValueError("scenario.planning must be a mapping")

        enabled = planning_values.get(
            "enabled",
            scenario.get("planning_enabled", False),
        )
        if not isinstance(enabled, bool):
            raise ValueError("planning.enabled must be a boolean")

        strategies = planning_values.get("strategies", DEFAULT_STRATEGIES)
        if not isinstance(strategies, list) or not all(
            isinstance(strategy, str) for strategy in strategies
        ):
            raise ValueError("planning.strategies must be a list of strings")
        unsupported = [strategy for strategy in strategies if strategy not in SUPPORTED_STRATEGIES]
        if unsupported:
            raise ValueError(f"Unsupported planning strategies: {', '.join(unsupported)}")

        speeds = planning_values.get(
            "fixed_speed_values_mph",
            DEFAULT_FIXED_SPEED_VALUES_MPH,
        )
        if not isinstance(speeds, list) or any(
            isinstance(speed, bool) or not isinstance(speed, (int, float))
            for speed in speeds
        ):
            raise ValueError("planning.fixed_speed_values_mph must be a list of numbers")
        if any(speed <= 0 or int(speed) != speed for speed in speeds):
            raise ValueError("planning.fixed_speed_values_mph must contain positive integers")

        return PlanningConfig(
            enabled=enabled,
            strategies=list(strategies),
            fixed_speed_values_mph=[int(speed) for speed in speeds],
        )

    @staticmethod
    def _mapping(
        values: dict[str, Any],
        key: str,
        *,
        required: bool = True,
    ) -> dict[str, Any]:
        section = values.get(key)
        if section is None and not required:
            return {}
        if not isinstance(section, dict):
            raise ValueError(f"scenario.{key} must be a mapping")
        return section

    @staticmethod
    def _required_string(values: dict[str, Any], key: str) -> str:
        value = values.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"scenario.{key} must be a non-empty string")
        return value


def load_scenario(
    scenario_path: str | Path,
    repo_root: str | Path | None = None,
) -> LoadedScenario:
    return ScenarioLoader(scenario_path, repo_root=repo_root).load()
