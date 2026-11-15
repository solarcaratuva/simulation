# Parameters Needed

Why: sim looks precise but inputs are guesses. This lists every `CarConfig` value, its unit, owner, and source. Fix values here before tuning code.

Sources: `sim/config.py` (`CarConfig`), `car_params.json`, used in `sim/physics.py`.
How to update: edit table cell, change `source` from `unknown` when confirmed.

## Car params (all 10 used by sim)

| Param | Value now | Unit | Owner | Source | Effect |
|---|---|---|---|---|---|
| `mass` | 337 | kg | Mechanical | unknown — confirm weigh-in | Heavier = more rolling + regen energy |
| `battery_capacity` | 5000 | Wh | Electrical | unknown — confirm pack spec | Bigger = more laps, slower SoC drop |
| `solar_panel_area` | 4 | m² | Electrical | unknown — confirm array size | Bigger = more solar power |
| `solar_panel_efficiency` | 0.23 | constant (NA)| Electrical | unknown — confirm datasheet | Higher = more solar power |
| `electrical_efficiency` | 0.99 | constant (NA) | Electrical | unknown — confirm MPPT/motor | BUG? (`physics.py:21`) multiplies, should divide |
| `C_dA` | 0.73809 | m² | Mechanical | unknown — confirm aero test/CFD | Higher = more drag, slower optimal speed |
| `tire_pressure` | 5 | bar | Mechanical | unknown — confirm actual pressure | Higher = less rolling resistance in current formula |
| `regen_efficiency` | 0.5 | fraction | Electrical | unknown — confirm | Higher = more energy back on slowdown |
| `rho` | 1.192 | kg/m³ | Software | estimate — std air | Higher = more drag |
| `g` | 9.80665 | m/s² | Software | measured — constant | Fixed, do not change |

## Ignored keys in `car_params.json` (not read by `CarConfig.from_json`)

| Key | Value | Action |
|---|---|---|
| `wheels` | 4 | Delete or use? Not in physics |
| `battery_voltage` | `"inf"` | V | Delete or use? Never read |
| `v_starting` | 90 | km/h | Delete or use? Never read |

