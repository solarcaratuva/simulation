# Parameter Schema

How every car value should be stored: number + unit + error + source. Future replacement for flat `car_params.json`.

Docs-only. No code changes. See `parameters_needed.md` for the short table.

## Required fields (every parameter)

| Field | Allowed values | Example |
|---|---|---|
| `value` | number, or `null` if not yet known | `337` |
| `unit` | SI unit, or `fraction` for 0–1 | `kg` |
| `uncertainty` | ± same unit, or `null` if unknown | `5` |
| `source` | `measured` / `datasheet` / `estimate` / `unknown` | `measured` |
| `confidence` | `low` / `medium` / `high` — only these three | `medium` |
| `last_updated` | `YYYY-MM-DD`, or `null` | `2026-09-01` |
| `owner` | `Electrical` / `Mechanical` / `Software` | `Mechanical` |
| `notes` | 1 line: how it was got, what to check | `Weigh-in with driver` |

`high` = measured on car or datasheet. `medium` = good estimate. `low` = guess.

## Full example

```json
{
  "mass": {
    "value": 337,
    "unit": "kg",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Mechanical",
    "notes": "Confirm weigh-in with driver. Heavier = more rolling loss."
  },
  "battery_capacity": {
    "value": 5000,
    "unit": "Wh",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Confirm pack spec, usable vs nameplate. Bigger = more laps."
  },
  "solar_panel_area": {
    "value": 4,
    "unit": "m^2",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Confirm array size. Bigger = more solar power."
  },
  "solar_panel_efficiency": {
    "value": 0.23,
    "unit": "fraction",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Confirm cell datasheet. Higher = more solar power."
  },
  "electrical_efficiency": {
    "value": 0.99,
    "unit": "fraction",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Covers all losses in one number. BUG? physics.py multiplies, should divide."
  },
  "mppt_efficiency": {
    "value": null,
    "unit": "fraction",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Not in sim yet. Split out of electrical_efficiency when measured."
  },
  "C_dA": {
    "value": 0.73809,
    "unit": "m^2",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Mechanical",
    "notes": "Drag coeff x frontal area. Confirm aero test or CFD."
  },
  "tire_pressure": {
    "value": 5,
    "unit": "bar",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Mechanical",
    "notes": "Confirm actual pressure. Higher = less rolling loss in formula."
  },
  "regen_efficiency": {
    "value": 0.5,
    "unit": "fraction",
    "uncertainty": null,
    "source": "unknown",
    "confidence": "low",
    "last_updated": null,
    "owner": "Electrical",
    "notes": "Confirm. Higher = more energy back on slowdown."
  },
  "rho": {
    "value": 1.192,
    "unit": "kg/m^3",
    "uncertainty": null,
    "source": "estimate",
    "confidence": "medium",
    "last_updated": null,
    "owner": "Software",
    "notes": "Standard air. Varies with weather, fine as const for now."
  },
  "g": {
    "value": 9.80665,
    "unit": "m/s^2",
    "uncertainty": null,
    "source": "measured",
    "confidence": "high",
    "last_updated": null,
    "owner": "Software",
    "notes": "Constant. Do not change."
  }
}
```

Ignored keys in `car_params.json` today (`wheels`, `battery_voltage`, `v_starting`) are left out — not read by sim. Add them in this format only if wired into physics.

