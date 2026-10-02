"""Tests for weather-induced dynamic travel degradation."""

from simulation.world_generator import WeatherSeverity, WeatherState
from simulation.weather_generator import WeatherGenerator
from simulation.world_generator import WorldGenerator


def test_weather_dynamic_delay_calculation():
    weather_gen = WeatherGenerator(seed=42)
    world = WorldGenerator(seed=42).generate_world()

    # Route R-06 is a high-altitude pass with high weather sensitivity
    route = world.routes["ROUTE_R_06"]
    base_hours = route.base_travel_hours

    # Test NORMAL weather
    w_normal = WeatherState(
        region="NORTHERN_SECTOR",
        timestamp_hour=10,
        temperature=5.0,
        rainfall=0.0,
        wind_speed=15.0,
        visibility=12.0,
        severity=WeatherSeverity.NORMAL,
    )
    time_normal = weather_gen.calculate_effective_travel_time(route, w_normal)
    assert time_normal == base_hours

    # Test MODERATE weather
    w_moderate = WeatherState(
        region="NORTHERN_SECTOR",
        timestamp_hour=10,
        temperature=-5.0,
        rainfall=8.0,
        wind_speed=50.0,
        visibility=3.5,
        severity=WeatherSeverity.MODERATE,
    )
    time_moderate = weather_gen.calculate_effective_travel_time(route, w_moderate)
    assert time_moderate > time_normal

    # Test SEVERE weather (blizzard)
    w_severe = WeatherState(
        region="NORTHERN_SECTOR",
        timestamp_hour=10,
        temperature=-22.0,
        rainfall=20.0,
        wind_speed=80.0,
        visibility=0.8,
        severity=WeatherSeverity.SEVERE,
    )
    time_severe = weather_gen.calculate_effective_travel_time(route, w_severe)
    assert time_severe > time_moderate
    assert time_severe >= base_hours * 2.0
