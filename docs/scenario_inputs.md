# Pre-Race Simulation Scenario Inputs

This document defines the inputs needed to run a pre-race simulation and planning study.

## Required Inputs

### Car Parameter File

**Source:** `Simulator/car_params.json`

The car parameter file is loaded through `CarConfig.from_json()` in `sim/config.py`.

The file may define:

- `mass`: Vehicle mass in kilograms.
- `battery_capacity`: Battery capacity in watt-hours.
- `solar_panel_area`: Solar panel area in square meters.
- `solar_panel_efficiency`: Solar conversion efficiency.
- `electrical_efficiency`: Electrical drivetrain efficiency.
- `C_dA`: Aerodynamic drag-area coefficient.
- `tire_pressure`: Tire pressure used to estimate rolling resistance.
- `regen_efficiency`: Regenerative braking efficiency.
- `rho`: Air density.
- `g`: Gravitational acceleration.

These values affect energy consumption, solar generation, regenerative braking, achievable speed, final state of charge (SOC), and total laps.

If the file is missing, the simulator uses the default `CarConfig` values. For reproducible planning results, provide an explicit car parameter file.

### Tracks

**Source:** `TrackConfig` in `sim/config.py`

A course requires:

- `name`: Human-readable course name.
- `file_path_name`: Filename-safe identifier for output files.
- `location`: Human-readable geographic location.
- `latitude` and `longitude`: Coordinates used for weather data.
- `lap_distance_km`: Course lap length.
- `timezone`: Local timezone used for weather timestamps.

The selected course affects:

- Weather retrieved from the Open-Meteo API.
- Solar energy available during the race.
- Distance accumulated per lap.
- Report and plot labels.
- Output filenames.

The CLI supports these course identifiers:

- `shenandoah_speedway`
- `virginia_international_raceway`
- `brainerd_international_raceway`

A course can be selected interactively or with `--location`.

### Race Start and End Time

**Configuration:** `RaceConfig.start_time_hour` and `RaceConfig.end_time_hour`

The default race window is:

- Start: `10.0` local hours
- End: `18.0` local hours

The race window determines:

- How many simulation timesteps are generated.
- Which weather interval is selected.
- How much sunlight is available.
- The total time available to complete laps.

The Open-Meteo weather path requires complete weather coverage for the selected time window.

### Initial SOC

**Configuration:** `RaceConfig.start_soc`

The default is `1.0`, representing 100% battery charge.

Initial SOC determines the energy available at race start. A lower initial SOC generally reduces achievable speed and total distance and increases the likelihood of reaching the minimum SOC threshold early.

### Weather Assumptions

Weather is controlled by `LapsRaceSimulator` and `WeatherService` in `sim/weather.py`.

By default, the simulator attempts to retrieve:

- Shortwave solar radiation, used as GHI.
- Cloud cover.

Weather is requested using the selected course's coordinates and timezone.

If the API request fails, the simulator falls back to synthetic weather. Synthetic weather uses a daylight-shaped solar curve and randomized cloud cover.

Set `use_api_weather=False` when deterministic synthetic weather is preferred, such as for repeatable tests. Planning sweeps also support a synthetic weather seed.

Weather affects:

- Solar charging.
- The ideal SOC trajectory.
- The calculated feasible baseline speed.
- Controller speed adjustments.
- Final SOC and total laps.

## Optional Inputs

### Target and Minimum SOC

**Configuration:** `RaceConfig.target_soc` and `RaceConfig.min_soc`

Defaults:

- Target SOC: `0.10`
- Minimum SOC: `0.10`

`target_soc` is the planned ending SOC used when calculating the energy budget and ideal SOC trajectory.

`min_soc` is the operational lower bound. If the vehicle reaches it, the simulation stops early and records when it happened.

### Strategy

**Configuration:** `RaceConfig.strategy`

Available strategies:

- `pi`: Continuous proportional-integral SOC feedback.
- `stepped`: Discrete speed changes based on SOC error.
- `interval-hold`: Recomputes a feasible speed periodically and holds it between updates.
- `fixed`: Maintains a configured fixed speed.

The strategy affects how speed responds to SOC and weather conditions.

### Aggressiveness

**Configuration:** `RaceConfig.aggressiveness`

Aggressiveness controls the size of controller responses. Higher values generally produce stronger speed changes when SOC differs from its target trajectory.

Default planning values are defined in `sim/planning/sweep.py`:

- `pi`: `1.5`
- `stepped`: `1.2`
- `interval-hold`: `1.0`
- `fixed`: `1.0`

### Energy Safety Scale

**Configuration:** `RaceConfig.energy_safety_scale`

Default: `1.0`

This scales the calculated energy budget. Lower values reserve more energy and produce a more conservative speed plan.

Values are constrained to the range `0.01` through `1.0`.

### Speed Limits and Initial Speed

**Configuration:** `RaceConfig`

Optional speed settings include:

- `initial_speed_mps`
- `fixed_speed_mps`
- `min_speed_mps`
- `max_speed_mps`

The minimum and maximum speeds constrain controller output. `fixed_speed_mps` is used by the fixed-speed strategy and fixed-speed planning sweep.

### Simulation Timestep

**Configuration:** `RaceConfig.time_step_minutes`

Default: `1.0` minute.

A smaller timestep provides more frequent controller updates and finer timing resolution but requires more simulation steps.

## Expected Planning Outputs

The planning study in `sim/planning/sweep.py` produces two comparisons:

1. A fixed-speed sweep across configured speeds.
2. A strategy sweep across the available strategies.

Each planning result includes:

- Strategy or fixed speed.
- Total laps.
- Total distance in miles.
- Final SOC percentage.
- Minimum SOC percentage.
- Average speed.
- Maximum and minimum speed.
- Whether the full race window was completed.
- Whether the simulation reached minimum SOC early.

The planning report in `sim/planning/report.py` summarizes:

- Best fixed speed.
- Strategy comparison.
- Whether each strategy completed the race or reached minimum SOC.
- A recommended speed or strategy.

A normal simulation also produces:

- SOC plot.
- Speed plot.
- Weather plot.
- Race dashboard.
- Text summary of race performance.

## Example Scenario

```text
Course:
  Virginia International Raceway (Patriot Course)
  Identifier: virginia_international_raceway
  Lap distance: 1.77 km
  Timezone: America/New_York

Car:
  Load parameters from car_params.json

Race window:
  Start: 10:00 local time
  End: 18:00 local time

Battery:
  Initial SOC: 100%
  Target SOC: 10%
  Minimum SOC: 10%

Weather:
  Use Open-Meteo forecast data
  Fall back to synthetic weather if the API is unavailable

Strategy:
  interval-hold
  Aggressiveness: 1.0
  Energy safety scale: 1.0
  Timestep: 1 minute

Planning study:
  Run the fixed-speed sweep
  Compare pi, stepped, interval-hold, and fixed strategies

Expected outputs:
  Best fixed speed
  Strategy comparison
  Recommended strategy
  Expected laps
  Final SOC
  Whether the full eight-hour window is completed