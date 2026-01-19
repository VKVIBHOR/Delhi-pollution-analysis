"""
Data Layer: Emission Sources and Weather Models

Provides synthetic but realistic data for fair policy comparisons.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
from backend.config import (
    EMISSIONS, WEATHER_DEFAULTS, BASELINE_PM,
    DISPERSION_RATES, HOURS_PER_DAY
)


@dataclass
class EmissionProfile:
    """Hourly emission profile for a source category."""
    source_name: str
    pm25_rate: float  # µg/m³ per hour
    pm10_rate: float
    is_controllable: bool = True
    
    def get_hourly_emissions(self, hour: int, modifiers: Dict = None) -> Dict[str, float]:
        """
        Get emissions for a specific hour with optional modifiers.
        
        Args:
            hour: Hour of day (0-23)
            modifiers: Dict with reduction factors (0-1) for each pollutant
        
        Returns:
            Dict with pm25 and pm10 emission values
        """
        modifiers = modifiers or {}
        
        # Apply time-of-day variation
        time_factor = self._get_time_factor(hour)
        
        pm25 = self.pm25_rate * time_factor * (1 - modifiers.get("pm25", 0))
        pm10 = self.pm10_rate * time_factor * (1 - modifiers.get("pm10", 0))
        
        return {"pm25": pm25, "pm10": pm10}
    
    def _get_time_factor(self, hour: int) -> float:
        """
        Emissions vary by time of day.
        Peak hours: 8-10 AM and 6-9 PM (traffic)
        Low hours: 2-5 AM
        """
        if self.source_name == "vehicles":
            if 8 <= hour <= 10 or 18 <= hour <= 21:
                return 1.5  # Rush hour
            elif 2 <= hour <= 5:
                return 0.3  # Night
            else:
                return 1.0
        elif self.source_name == "construction":
            if 9 <= hour <= 17:
                return 1.2  # Working hours
            else:
                return 0.2  # Night/early morning
        elif self.source_name == "industry":
            return 1.0  # 24/7 operation
        elif self.source_name == "external":
            # Crop burning peaks in morning
            if 5 <= hour <= 9:
                return 1.8
            else:
                return 0.8
        else:
            return 1.0


@dataclass
class WeatherCondition:
    """Weather state affecting pollution dispersion."""
    wind_speed: float  # km/h
    wind_direction: float  # degrees
    temperature: float  # °C
    humidity: float  # %
    inversion: bool  # Temperature inversion
    
    def get_dispersion_rate(self) -> float:
        """
        Calculate hourly dispersion rate based on weather.
        
        Returns:
            Fraction of PM that disperses naturally per hour
        """
        base = DISPERSION_RATES["base_rate"]
        
        # Wind helps dispersion
        wind_bonus = DISPERSION_RATES["wind_factor"] * self.wind_speed
        
        # Humidity helps deposition
        if self.humidity > 70:
            humidity_bonus = DISPERSION_RATES["humidity_deposition"]
        else:
            humidity_bonus = 0
        
        # Temperature inversion traps pollution
        if self.inversion:
            total = (base + wind_bonus + humidity_bonus) * DISPERSION_RATES["inversion_multiplier"]
        else:
            total = base + wind_bonus + humidity_bonus
        
        return min(total, 0.20)  # Cap at 20% per hour
    
    def get_external_transport(self) -> Dict[str, float]:
        """
        Calculate pollution transported from outside Delhi based on wind.
        Wind from NW during crop burning season brings more pollution.
        
        Returns:
            Additional PM from regional transport
        """
        # NW winds (270-360 degrees) during Oct-Nov bring crop smoke
        if 270 <= self.wind_direction <= 360:
            transport_factor = 0.3 + (self.wind_speed / 30)  # Higher wind = more transport
        else:
            transport_factor = 0.1
        
        return {
            "pm25": EMISSIONS["external"]["pm25"] * transport_factor,
            "pm10": EMISSIONS["external"]["pm10"] * transport_factor,
        }


class EmissionSourceManager:
    """Manages all emission sources for the simulation."""
    
    def __init__(self):
        self.sources: Dict[str, EmissionProfile] = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Create emission profiles for all sources."""
        for name, data in EMISSIONS.items():
            self.sources[name] = EmissionProfile(
                source_name=name,
                pm25_rate=data["pm25"],
                pm10_rate=data["pm10"],
                is_controllable=data.get("controllable", True),
            )
    
    def get_total_emissions(
        self, 
        hour: int, 
        policy_modifiers: Dict[str, Dict] = None
    ) -> Dict[str, float]:
        """
        Get total emissions from all sources for a given hour.
        
        Args:
            hour: Hour of day (0-23)
            policy_modifiers: Dict mapping source names to reduction factors
        
        Returns:
            Total PM2.5 and PM10 emissions
        """
        policy_modifiers = policy_modifiers or {}
        
        total_pm25 = 0.0
        total_pm10 = 0.0
        
        for name, source in self.sources.items():
            modifiers = policy_modifiers.get(name, {})
            emissions = source.get_hourly_emissions(hour, modifiers)
            total_pm25 += emissions["pm25"]
            total_pm10 += emissions["pm10"]
        
        return {"pm25": total_pm25, "pm10": total_pm10}
    
    def get_source_breakdown(self, hour: int = 12) -> Dict[str, Dict]:
        """Get emission breakdown by source (for visualization)."""
        breakdown = {}
        for name, source in self.sources.items():
            emissions = source.get_hourly_emissions(hour)
            breakdown[name] = {
                "pm25": emissions["pm25"],
                "pm10": emissions["pm10"],
                "controllable": source.is_controllable,
            }
        return breakdown


class WeatherScenarioGenerator:
    """Generate weather scenarios for simulations."""
    
    @staticmethod
    def get_default_weather() -> WeatherCondition:
        """Get typical Delhi winter weather (worst for pollution)."""
        return WeatherCondition(**WEATHER_DEFAULTS)
    
    @staticmethod
    def get_stagnant_weather() -> WeatherCondition:
        """Worst-case: low wind, inversion, high humidity."""
        return WeatherCondition(
            wind_speed=2.0,
            wind_direction=0,
            temperature=12,
            humidity=85,
            inversion=True,
        )
    
    @staticmethod
    def get_favorable_weather() -> WeatherCondition:
        """Best-case: high wind, no inversion."""
        return WeatherCondition(
            wind_speed=20.0,
            wind_direction=180,  # From south (no crop burning)
            temperature=25,
            humidity=40,
            inversion=False,
        )
    
    @staticmethod
    def generate_realistic_sequence(days: int) -> List[WeatherCondition]:
        """
        Generate a realistic sequence of weather conditions.
        Includes random variation but maintains Delhi winter patterns.
        """
        np.random.seed(42)  # Reproducible
        weather_sequence = []
        
        for day in range(days):
            for hour in range(HOURS_PER_DAY):
                # Base conditions with daily and hourly variation
                base_wind = 6 + np.random.normal(0, 3)
                base_wind = max(1, min(25, base_wind))  # Clamp
                
                # Inversions more likely at night and early morning
                inversion_prob = 0.4 if 22 <= hour or hour <= 8 else 0.1
                inversion = np.random.random() < inversion_prob
                
                # Temperature varies through day
                temp = 15 + 8 * np.sin((hour - 6) * np.pi / 12)
                
                weather = WeatherCondition(
                    wind_speed=base_wind,
                    wind_direction=270 + np.random.normal(0, 30),
                    temperature=temp,
                    humidity=50 + np.random.normal(0, 15),
                    inversion=inversion,
                )
                weather_sequence.append(weather)
        
        return weather_sequence


# Convenience functions for API
def get_emission_sources() -> EmissionSourceManager:
    """Factory function to get emission source manager."""
    return EmissionSourceManager()


def get_weather_scenario(scenario_type: str = "default") -> List[WeatherCondition]:
    """Get weather scenario by type."""
    generator = WeatherScenarioGenerator()
    
    if scenario_type == "default":
        return [generator.get_default_weather()] * (30 * HOURS_PER_DAY)
    elif scenario_type == "stagnant":
        return [generator.get_stagnant_weather()] * (30 * HOURS_PER_DAY)
    elif scenario_type == "favorable":
        return [generator.get_favorable_weather()] * (30 * HOURS_PER_DAY)
    elif scenario_type == "realistic":
        return generator.generate_realistic_sequence(30)
    else:
        return [generator.get_default_weather()] * (30 * HOURS_PER_DAY)
