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

    # Current model multiplies resistance forces by velocity,
    # so power draw is zero when the car is stationary.
    assert math.isclose(physics.power_drained(0), 0.0)


def test_power_drained_increases_with_speed():
    physics = make_physics()

    power_at_10 = physics.power_drained(10)
    power_at_20 = physics.power_drained(20)

    assert power_at_20 > power_at_10


def test_solar_power_zero_at_zero_ghi():
    physics = make_physics()

    assert physics.solar_power(0) == 0


def test_solar_power_scales_with_ghi():
    physics = make_physics()

    power_at_500 = physics.solar_power(500)
    power_at_1000 = physics.solar_power(1000)

    assert math.isclose(power_at_1000, 2 * power_at_500)


def test_solar_power_scales_with_panel_area():
    car = CarConfig(
        solar_panel_area=4,
        solar_panel_efficiency=0.25,
    )
    physics = PhysicsEngine(car)

    power_at_4 = physics.solar_power(1000)

    car.solar_panel_area = 8
    power_at_8 = physics.solar_power(1000)

    assert math.isclose(power_at_8, 2 * power_at_4)


def test_solar_power_scales_with_panel_efficiency():
    car = CarConfig(
        solar_panel_area=4,
        solar_panel_efficiency=0.20,
    )
    physics = PhysicsEngine(car)

    power_at_20 = physics.solar_power(1000)

    car.solar_panel_efficiency = 0.40
    power_at_40 = physics.solar_power(1000)

    assert math.isclose(power_at_40, 2 * power_at_20)