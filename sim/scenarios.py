"""Conservative / base / optimistic CarConfig variants from parameter uncertainty.

Each parameter is shifted by +/- its `uncertainty` in the direction that
worsens (conservative) or improves (optimistic) expected performance.
"""
import json
from dataclasses import fields
from typing import Dict

from sim.config import CarConfig

CONSERVATIVE = "conservative"
BASE = "base"
OPTIMISTIC = "optimistic"
SCENARIOS = (CONSERVATIVE, BASE, OPTIMISTIC)

# +1: conservative = value + uncertainty (bigger is worse for performance)
# -1: conservative = value - uncertainty (bigger is better for performance)
# Optimistic is always the opposite. Parameters not listed (e.g. g) are held fixed.
CONSERVATIVE_DIRECTION: Dict[str, int] = {
    "mass": +1,                    # heavier -> more rolling loss, more energy to accelerate
    "C_dA": +1,                    # more drag
    "rho": +1,                     # denser air -> more drag
    "battery_capacity": -1,        # less usable energy
    "solar_panel_area": -1,        # less solar power
    "solar_panel_efficiency": -1,  # less solar power
    "electrical_efficiency": -1,   # more losses (see note below)
    "tire_pressure": -1,           # lower pressure -> higher Crr
    "regen_efficiency": -1,        # less energy recovered
}
# NOTE: physics.py currently multiplies drain by electrical_efficiency, so a lower
# value reduces drain there. The direction above is the physical one; revisit
# if that formula is corrected to divide.

FRACTION_PARAMS = {"solar_panel_efficiency", "electrical_efficiency", "regen_efficiency"}


def _shift(name: str, value: float, uncertainty: float, sign: int) -> float:
    shifted = value + sign * CONSERVATIVE_DIRECTION[name] * uncertainty
    if name in FRACTION_PARAMS:
        shifted = min(max(shifted, 0.0), 1.0)
    return shifted


def make_scenario(params: Dict[str, dict], scenario: str) -> CarConfig:
    """Build one CarConfig from rich-schema params ({name: {"value", "uncertainty", ...}}).

    Missing parameters or null values fall back to CarConfig defaults; a null
    uncertainty is treated as 0.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; expected one of {SCENARIOS}")
    sign = {CONSERVATIVE: +1, BASE: 0, OPTIMISTIC: -1}[scenario]

    kwargs = {}
    for f in fields(CarConfig):
        entry = params.get(f.name)
        if not entry or entry.get("value") is None:
            continue
        value = entry["value"]
        uncertainty = entry.get("uncertainty") or 0.0
        if f.name in CONSERVATIVE_DIRECTION and sign != 0:
            value = _shift(f.name, value, uncertainty, sign)
        kwargs[f.name] = value
    return CarConfig(**kwargs)


def make_scenarios(params: Dict[str, dict]) -> Dict[str, CarConfig]:
    """Return {"conservative": ..., "base": ..., "optimistic": ...}."""
    return {s: make_scenario(params, s) for s in SCENARIOS}


def load_scenarios(filepath: str) -> Dict[str, CarConfig]:
    """Load a rich-schema parameter JSON file and build all three scenarios."""
    with open(filepath, "r") as f:
        return make_scenarios(json.load(f))
