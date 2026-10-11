# Pre-Race Simulation Scenario Inputs

This document separates inputs provided by a user from the configuration parameters that define a scenario.

## User-Defined Inputs

| User input | How it is provided | Maps to |
|---|---|---|
| Car parameters | `car_params.json` | `CarConfig` |
| Track | `--location` or prompt | `TrackConfig` |
| Strategy | `--strategy` or prompt | `RaceConfig.strategy` |
| Aggressiveness | `--aggressiveness` | `RaceConfig.aggressiveness` |
| Energy safety scale | Interactive prompt | `RaceConfig.energy_safety_scale` |
| Fixed-speed sweep | `--speed-sweep` | Planning settings |
| Planning study | `--plan` | Planning settings |
| Weather source | Currently set in code | Weather settings |
| Race times, SOC, speed limits, timestep | Currently set in code | `RaceConfig` |

*For Car Parameters, the program automatically searches in `car_params.json` in the project root and pulls the configs from there.*
## Config/Scenario Parameters

These are the fields a future scenario configuration should contain. Values marked optional can use the listed default.

### Car Configuration

Source: `car_params.json`

| Parameter | Units | Required | Affects |
|---|---:|---|---|
| `mass` | kg | Yes | Rolling resistance, Regen energy, total energy use |
| `battery_capacity` | Wh | Yes | Available battery energy, SOC changes |
| `solar_panel_area` | m² | Yes | Solar power collected |
| `solar_panel_efficiency` | fraction | Yes | Solar power collected |
| `electrical_efficiency` | fraction | Yes | Driving power consumption |
| `C_dA` | m² | Yes | Aerodynamic drag, energy use |
| `tire_pressure` | pressure units | Yes | Rolling resistance,  energy use |
| `regen_efficiency` | fraction | Yes | Regen energy |
| `rho` | kg/m³ | Yes | Aerodynamic drag |
| `g` | m/s² | Yes | Rolling resistance |

### Track Configuration

| Parameter | Units | Required | Affects |
|---|---:|---|---|
| `name` | text | Yes | Report and plot labels |
| `file_path_name` | text | Yes | Track identifier and output filenames |
| `location` | text | Yes | Human-readable location |
| `latitude`, `longitude` | degrees | Yes | Weather API location |
| `lap_distance_km` | km | Yes | Distance and lap count |
| `timezone` | IANA timezone | Yes | Local race and weather times |

Available track IDs: `shenandoah_speedway`, `virginia_international_raceway`, `brainerd_international_raceway`.

### Race and Battery Conditions

| Parameter | Units | Required | Default | Affects |
|---|---:|---|---:|---|
| `start_time_hour` | local hour | Yes | `10.0` | Race duration, weather window |
| `end_time_hour` | local hour | Yes | `18.0` | Race duration, weather window |
| `start_soc` | fraction | Yes | `1.0` | Starting energy, achievable distance |
| `target_soc` | fraction | No | `0.10` | Planned energy budget, SOC trajectory |
| `min_soc` | fraction | No | `0.10` | Early-stop safety threshold |
| `energy_safety_scale` | fraction | No | `1.0` | Energy reserve |

### Weather Configuration

| Parameter | Type | Required | Default | Affects |
|---|---|---|---|---|
| `source` | `api` / `synthetic` | Yes | API | Weather data used |
| `race_date` | date | No | Auto-selected | Forecast date |
| `random_seed` | integer | No | `7` in sweeps | Synthetic-weather generation |
| `GHI`, `cloud_cover` | weather data | Generated or API-provided | None | Solar charging, SOC trajectory |

The current API uses Open-Meteo shortwave radiation and cloud cover. API failure falls back to synthetic weather.

### Strategy and Speed

| Parameter | Units / values | Required | Default | Affects |
|---|---|---|---|---|
| `strategy` | `pi`, `stepped`, `interval-hold`, `fixed` | Yes | `pi` | Speed strategy |
| `aggressiveness` | scalar | No | Strategy-specific | Controller response strength |
| `fixed_speed_mps` | m/s | No | `15.0` | Fixed-strategy speed |
| `min_speed_mps` | m/s | No | `4.0` | Lower speed limit |
| `max_speed_mps` | m/s | No | `35.0` | Upper speed limit |
| `initial_speed_mps` | m/s | No | `20.0` | *Currently unused* |

Planning aggressiveness defaults: `pi=1.5`, `stepped=1.2`, `interval-hold=1.0`, `fixed=1.0`.

### Simulation and Planning

| Parameter | Type | Required | Default | Affects |
|---|---|---|---|---|
| `time_step_minutes` | minutes | No | `1.0` | Simulation update frequency |
| `use_api_weather` | boolean | No | `True` | Weather data source |
| `planning_enabled` | boolean | No | `False` | Single run versus planning study |
| `strategies` | list | No | All strategies | Strategies compared |
| `fixed_speed_values_mph` | list | No | `10`-`46`, step `2` | Speeds compared |

## Expected Planning Outputs

- Best fixed speed and strategy recommendation
- Total laps and distance
- Final and minimum SOC
- Average, minimum, and maximum speed
- Full-window completion status
- Time and laps when minimum SOC was reached

## YAML Scenario File Format

YAML is used for scenario files to represent nested race,
weather, and strategy settings clearly, and for convenient editing.

Each scenario file contains:

| Field | Required | Description |
|---|---|---|
| `scenario.name` | Yes | Human-readable scenario name |
| `scenario.car_parameter_file` | Yes | Path to the car parameter JSON file |
| `scenario.course_file` | Yes | Path to the course/track definition file |
| `scenario.race.start_time_hour` | Yes | Local race start time, expressed as decimal hours |
| `scenario.race.end_time_hour` | Yes | Local race end time, expressed as decimal hours |
| `scenario.race.start_soc` | Yes | Initial battery state of charge from `0.0` to `1.0` |
| `scenario.weather.source` | Yes | `synthetic` for offline weather or `api` for Open-Meteo |
| `scenario.weather.random_seed` | No | Seed for reproducible synthetic weather |
| `scenario.strategy.name` | Yes | `fixed`, `pi`, `stepped`, or `interval-hold` |
| `scenario.strategy.fixed_speed_mps` | For `fixed` | Constant target speed in metres per second |
| `scenario.strategy.aggressiveness` | No | Controller response strength |

The example below uses synthetic (offline) weather and the `fixed` strategy with a constant speed. More examples are in `scenarios_examples/`

```yaml
scenario:
  name: Shenandoah offline constant-speed planning
  car_parameter_file: car_params.json
  course_file: courses/shenandoah_speedway.json

  race:
    start_time_hour: 10.0
    end_time_hour: 18.0
    start_soc: 1.0
    target_soc: 0.10
    min_soc: 0.10

  weather:
    source: synthetic
    random_seed: 7

  strategy:
    name: fixed
    fixed_speed_mps: 15.0
    aggressiveness: 1.0

  simulation:
    time_step_minutes: 1.0
```