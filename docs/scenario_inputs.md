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
| `mass` | kg | Yes | Rolling resistance, regenerative energy, total energy use |
| `battery_capacity` | Wh | Yes | Available battery energy and SOC changes |
| `solar_panel_area` | m² | Yes | Solar power collected |
| `solar_panel_efficiency` | fraction | Yes | Solar power collected |
| `electrical_efficiency` | fraction | Yes | Driving power consumption |
| `C_dA` | m² | Yes | Aerodynamic drag and speed energy use |
| `tire_pressure` | pressure units | Yes | Rolling resistance and energy use |
| `regen_efficiency` | fraction | Yes | Energy recovered during deceleration |
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
| `start_time_hour` | local hour | Yes | `10.0` | Race duration and weather window |
| `end_time_hour` | local hour | Yes | `18.0` | Race duration and weather window |
| `start_soc` | fraction | Yes | `1.0` | Starting energy and achievable distance |
| `target_soc` | fraction | No | `0.10` | Planned energy budget and SOC trajectory |
| `min_soc` | fraction | No | `0.10` | Early-stop safety threshold |
| `energy_safety_scale` | fraction | No | `1.0` | Energy reserve and conservatism |

### Weather Configuration

| Parameter | Type | Required | Default | Affects |
|---|---|---|---|---|
| `source` | `api` / `synthetic` / `file` | Yes | API | Weather data used |
| `race_date` | date | No | Auto-selected | Forecast date |
| `weather_file` | path | No | None | User-provided GHI and cloud data |
| `random_seed` | integer | No | `7` in sweeps | Synthetic-weather repeatability |
| `GHI`, `cloud_cover` | weather data | File source only | None | Solar charging and SOC trajectory |

The current API uses Open-Meteo shortwave radiation and cloud cover. API failure falls back to synthetic weather.

### Strategy and Speed

| Parameter | Units / values | Required | Default | Affects |
|---|---|---|---|---|
| `strategy` | `pi`, `stepped`, `interval-hold`, `fixed` | Yes | `pi` | Speed response to SOC and weather |
| `aggressiveness` | scalar | No | Strategy-specific | Controller response strength |
| `fixed_speed_mps` | m/s | No | `15.0` | Fixed-strategy speed |
| `min_speed_mps` | m/s | No | `4.0` | Lower speed limit |
| `max_speed_mps` | m/s | No | `35.0` | Upper speed limit |
| `initial_speed_mps` | m/s | No | `20.0` | Currently unused |

Planning aggressiveness defaults: `pi=1.5`, `stepped=1.2`, `interval-hold=1.0`, `fixed=1.0`.

### Simulation and Planning

| Parameter | Type | Required | Default | Affects |
|---|---|---|---|---|
| `time_step_minutes` | minutes | No | `1.0` | Simulation resolution and update frequency |
| `use_api_weather` | boolean | No | `True` | API versus synthetic weather |
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
