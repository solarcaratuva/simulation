"""Shared unit conversions. The simulator works in SI internally (m, m/s, s);
these helpers are for display and for converting user-facing inputs."""

MPH_PER_MPS = 2.237
METERS_PER_MILE = 1609.34
METERS_PER_KM = 1000.0
SECONDS_PER_MINUTE = 60.0
MINUTES_PER_HOUR = 60.0


def mph_to_mps(mph):
    return mph / MPH_PER_MPS


def mps_to_mph(mps):
    return mps * MPH_PER_MPS


def meters_to_miles(meters):
    return meters / METERS_PER_MILE


def meters_to_km(meters):
    return meters / METERS_PER_KM


def km_to_meters(km):
    return km * METERS_PER_KM


def minutes_to_hours(minutes):
    return minutes / MINUTES_PER_HOUR


def minutes_to_seconds(minutes):
    return minutes * SECONDS_PER_MINUTE
