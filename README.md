# Solar Car Simulator

This project simulates solar car laps races so the team can test strategy ideas
before race day. The current focus is **pre-race planning**: comparing speeds,
controllers, weather assumptions, and energy margins before the car is on track.

The codebase is still evolving. File names and package structure may change as
the simulator becomes more mature, but the concepts in this README should stay
useful.

## What This Tool Is For

Use the simulator to answer questions like:

- How many laps should we expect under a given forecast?
- What fixed speed is safe?
- Which strategy/controller performs best for a track and race window?
- How much battery margin do we have at the end of the race?
- What happens if solar input is worse than expected?

The simulator is a planning aid. It should support strategy discussion, not
replace engineering judgment, driver feedback, or race-day telemetry.

## Current Capabilities

The project currently supports:

- Single simulated race runs
- Fixed-speed sweeps
- Strategy/controller comparisons
- MVP pre-race planning reports
- Weather forecasts from Open-Meteo, with synthetic fallback weather
- Plot generation for individual runs

There is also an early live-race script in the repo, but active development is
currently centered on pre-race simulation and planning.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Run the main simulator CLI:

```bash
python3 sim/main.py
```

You will be prompted to choose a track and strategy. The simulator will run one
race simulation, print a summary, and save plots.

Run the pre-race planning workflow:

```bash
python3 sim/main.py --plan
```

Run only the fixed-speed sweep:

```bash
python3 sim/main.py --speed-sweep
```

Run a specific strategy:

```bash
python3 sim/main.py --strategy interval-hold
```

Other examples:

```bash
python3 sim/main.py --strategy pi --aggressiveness 0.9
python3 sim/main.py --strategy stepped --aggressiveness 1.0
python3 sim/main.py --strategy fixed
```

## Core Concepts

### Race Simulation

A race simulation models the car over a race window. At each timestep, it
estimates solar input, power draw, battery state of charge, distance traveled,
speed, and laps completed.

The output is a simulated race result: laps, distance, final battery state,
speed profile, weather profile, and other planning metrics.

### Pre-Race Planning

Pre-race planning runs many simulations and compares the outcomes. Instead of
asking “what happens for this one strategy?”, planning mode asks “which option
looks best across a set of reasonable choices?”

The current planning workflow compares:

- Fixed speeds
- Available strategy controllers
- Final state of charge
- Lap count
- Whether the car reached minimum SoC early

This area is expected to change the most as the team adds better strategy
ranking, uncertainty modeling, saved reports, and scenario configuration.

### Strategy Controllers

Strategies decide what speed the simulated car should target as the race
progresses.

Current strategy types include:

- `fixed`: hold a fixed speed
- `pi`: continuously adjust speed based on SoC error
- `stepped`: adjust speed using simple threshold rules
- `interval-hold`: periodically replan speed, then hold it between updates

These strategy names may evolve, but the design goal should remain the same:
make strategies easy to compare under the same car, track, race, and weather
assumptions.

### Weather

The simulator tries to use forecast data from Open-Meteo. If weather data cannot
be fetched, it falls back to generated synthetic weather.

This fallback is useful for development and offline testing, but real planning
should use the best available forecast and should eventually include uncertainty
checks.

### Car Parameters

Vehicle parameters are loaded from:

```text
car_params.json
```

Typical parameters include mass, battery capacity, solar panel area, solar panel
efficiency, drag, rolling resistance inputs, and regenerative braking
efficiency.

These values have a large effect on simulation output. Keep them up to date as
the car changes.

## Outputs

Single simulation runs print a summary and save plots. Plot output is currently
written under:

```text
plots/
```

Common plots include:

- Battery state of charge
- Speed over time
- Weather and solar input
- Combined race dashboard

Planning mode currently prints a terminal report. Saved planning artifacts such
as CSV, JSON, or Markdown reports are a natural next step.

## Interpreting Results

For strategy planning, do not look only at lap count. A useful plan should also
consider:

- Final SoC relative to the target
- Whether the car ever hit minimum SoC
- How much energy was left unused
- How sensitive the result is to weather assumptions
- Whether the recommended speed behavior is realistic for the team and driver

An option that finishes with very high SoC may be too conservative. An option
that finishes exactly at the minimum may be too risky. The best plan usually
balances lap count with a reasonable battery margin.

## Known MVP Limitations

The pre-race planning workflow is still early. Known limitations include:

- Recommendation ranking is basic and may prefer overly conservative results.
- Some edge cases around lap counting and timestep size still need attention.
- Planning reports are printed but not yet saved as structured artifacts.
- Weather uncertainty is not yet modeled deeply.
- Scenario configuration is still mostly handled through code and CLI options.

Treat current planning reports as useful comparisons, not final strategy
recommendations.

## Development Workflow

Run a syntax check:

```bash
python3 -m compileall sim
```

Run planning mode with the default track selection:

```bash
printf '\n' | python3 sim/main.py --plan
```

Run a fixed-speed sweep using the first track:

```bash
printf '1\n' | python3 sim/main.py --speed-sweep
```

## Code Organization

The exact file structure is expected to change. At a high level, the project is
organized around these responsibilities:

- Configuration: car, track, and race inputs
- Physics: vehicle power use, solar input, battery behavior
- Weather: forecast loading and fallback data
- Simulation: race loop and result generation
- Strategies: speed-control logic
- Planning: sweeps, comparisons, and recommendations
- Reporting/visualization: summaries and plots

When adding new functionality, try to keep those responsibilities separate.
Command-line files should mostly orchestrate work; simulation and strategy logic
should live in reusable modules.

## Deprecated Code

Older simulator implementations are kept in `deprecated/` for reference. New
development should use the active simulator code unless there is a specific
reason to recover an idea from an older file.

## Near-Term Priorities

The most important next improvements are:

1. Improve planning recommendation scoring so it prefers useful energy usage,
   not simply the highest final SoC.
2. Tighten lap-counting behavior for short tracks and high speeds.
3. Add tests for planning comparisons and simulation edge cases.
4. Add saved planning reports.
5. Add better scenario and weather-uncertainty workflows.
