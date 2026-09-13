# At zero speed, both aerodynamic/rolling force power terms are multiplied
# by velocity, so the current model produces zero power draw.
import math

from sim.config import CarConfig
from sim.physics import PhysicsEngine


def make_physics():
    car = CarConfig(
        mass=337,
        C_dA=0.73809,
        tire_pressure=5,
        rho=1.192,
        g=9.80665,
        electrical_efficiency=0.99,
    )
    return PhysicsEngine(car)


def test_force_drag_zero_at_zero_speed():
    physics = make_physics()

    assert physics.force_drag(0) == 0


def test_force_drag_scales_with_speed_squared():
    physics = make_physics()

    force_at_10 = physics.force_drag(10)
    force_at_20 = physics.force_drag(20)

    assert math.isclose(force_at_20, 4 * force_at_10)


def test_force_rolling_resistance_is_positive():
    physics = make_physics()

    assert physics.force_rolling_resistance(10) > 0


def test_power_drained_is_zero_at_zero_speed():
    physics = make_physics()

    assert math.isclose(physics.power_drained(0), 0.0)


def test_power_drained_increases_with_speed():
    physics = make_physics()

    power_at_10 = physics.power_drained(10)
    power_at_20 = physics.power_drained(20)

    assert power_at_20 > power_at_10