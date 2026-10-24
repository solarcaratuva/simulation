import unittest

from sim.config import CarConfig
from sim.scenarios import CONSERVATIVE_DIRECTION, make_scenario, make_scenarios


def _params():
    return {
        "mass": {"value": 300, "uncertainty": 10},
        "battery_capacity": {"value": 5000, "uncertainty": 200},
        "solar_panel_area": {"value": 4, "uncertainty": 0.2},
        "solar_panel_efficiency": {"value": 0.23, "uncertainty": 0.01},
        "electrical_efficiency": {"value": 0.99, "uncertainty": 0.02},
        "C_dA": {"value": 0.7, "uncertainty": 0.05},
        "tire_pressure": {"value": 5, "uncertainty": 0.5},
        "regen_efficiency": {"value": 0.5, "uncertainty": 0.1},
        "rho": {"value": 1.2, "uncertainty": 0.05},
        "g": {"value": 9.80665, "uncertainty": None},
    }


class TestScenarios(unittest.TestCase):

    def test_returns_three_car_configs(self):
        s = make_scenarios(_params())
        self.assertEqual(set(s), {"conservative", "base", "optimistic"})
        for cfg in s.values():
            self.assertIsInstance(cfg, CarConfig)

    def test_base_uses_nominal_values(self):
        base = make_scenario(_params(), "base")
        self.assertEqual(base.mass, 300)
        self.assertEqual(base.battery_capacity, 5000)

    def test_mass_direction(self):
        s = make_scenarios(_params())
        self.assertEqual(s["conservative"].mass, 310)
        self.assertEqual(s["optimistic"].mass, 290)

    def test_battery_capacity_direction(self):
        s = make_scenarios(_params())
        self.assertEqual(s["conservative"].battery_capacity, 4800)
        self.assertEqual(s["optimistic"].battery_capacity, 5200)

    def test_every_directional_param_ordered(self):
        s = make_scenarios(_params())
        for name, direction in CONSERVATIVE_DIRECTION.items():
            cons = getattr(s["conservative"], name)
            base = getattr(s["base"], name)
            opt = getattr(s["optimistic"], name)
            if direction > 0:
                self.assertGreater(cons, base, name)
                self.assertLess(opt, base, name)
            else:
                self.assertLess(cons, base, name)
                self.assertGreater(opt, base, name)

    def test_g_is_not_shifted(self):
        s = make_scenarios(_params())
        self.assertEqual(s["conservative"].g, s["optimistic"].g)

    def test_null_uncertainty_treated_as_zero(self):
        p = _params()
        p["mass"]["uncertainty"] = None
        s = make_scenarios(p)
        self.assertEqual(s["conservative"].mass, 300)
        self.assertEqual(s["optimistic"].mass, 300)

    def test_missing_or_null_value_uses_default(self):
        p = _params()
        del p["mass"]
        p["rho"]["value"] = None
        cfg = make_scenario(p, "conservative")
        self.assertEqual(cfg.mass, CarConfig().mass)
        self.assertEqual(cfg.rho, CarConfig().rho)

    def test_fractions_clamped(self):
        p = _params()
        p["electrical_efficiency"] = {"value": 0.99, "uncertainty": 0.5}
        s = make_scenarios(p)
        self.assertEqual(s["optimistic"].electrical_efficiency, 1.0)
        p["regen_efficiency"] = {"value": 0.1, "uncertainty": 0.5}
        self.assertEqual(make_scenario(p, "conservative").regen_efficiency, 0.0)

    def test_unknown_scenario_raises(self):
        with self.assertRaises(ValueError):
            make_scenario(_params(), "wild")


if __name__ == "__main__":
    unittest.main()
