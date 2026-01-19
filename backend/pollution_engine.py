"""
Pollution Dynamics Engine

Core simulation implementing the PM concentration evolution equation:
PM(t+1) = PM(t) + emissions - dispersion - deposition - policy_effects

This engine models:
- Hourly PM2.5 and PM10 concentration evolution
- Weather-dependent dispersion
- Policy intervention effects with decay/rebound
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from backend.config import BASELINE_PM, HOURS_PER_DAY, AQI_THRESHOLDS
from backend.data_layer import (
    EmissionSourceManager, 
    WeatherCondition,
    get_emission_sources,
)


@dataclass
class PollutionState:
    """Current state of pollution levels."""
    pm25: float
    pm10: float
    hour: int
    day: int
    
    def get_aqi_category(self) -> str:
        """Determine AQI category from PM2.5 level."""
        pm25 = self.pm25
        if pm25 <= AQI_THRESHOLDS["good"]["pm25"]:
            return "good"
        elif pm25 <= AQI_THRESHOLDS["satisfactory"]["pm25"]:
            return "satisfactory"
        elif pm25 <= AQI_THRESHOLDS["moderate"]["pm25"]:
            return "moderate"
        elif pm25 <= AQI_THRESHOLDS["poor"]["pm25"]:
            return "poor"
        elif pm25 <= AQI_THRESHOLDS["very_poor"]["pm25"]:
            return "very_poor"
        else:
            return "severe"
    
    def to_dict(self) -> Dict:
        return {
            "pm25": round(self.pm25, 2),
            "pm10": round(self.pm10, 2),
            "hour": self.hour,
            "day": self.day,
            "aqi_category": self.get_aqi_category(),
            "timestamp": f"Day {self.day}, Hour {self.hour:02d}:00",
        }


@dataclass
class PolicyEffect:
    """Represents the active effect of a policy."""
    policy_name: str
    source_modifiers: Dict[str, Dict[str, float]]  # source -> {pm25: reduction, pm10: reduction}
    direct_pm_reduction: Dict[str, float]  # Direct PM reduction (e.g., water spraying)
    hours_remaining: int
    decay_rate: float = 0.0  # Exponential decay per hour
    initial_strength: float = 1.0
    current_strength: float = 1.0
    
    def tick(self) -> bool:
        """
        Advance one hour. Returns True if effect is still active.
        """
        if self.decay_rate > 0:
            self.current_strength *= (1 - self.decay_rate)
        
        self.hours_remaining -= 1
        return self.hours_remaining > 0 and self.current_strength > 0.01
    
    def get_current_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Get source modifiers adjusted for current strength."""
        return {
            source: {
                pollutant: reduction * self.current_strength
                for pollutant, reduction in reductions.items()
            }
            for source, reductions in self.source_modifiers.items()
        }
    
    def get_current_direct_reduction(self) -> Dict[str, float]:
        """Get direct PM reduction adjusted for current strength."""
        return {
            pollutant: reduction * self.current_strength
            for pollutant, reduction in self.direct_pm_reduction.items()
        }


class PollutionDynamicsEngine:
    """
    Main simulation engine for pollution dynamics.
    
    Implements the core equation:
    PM(t+1) = PM(t) + emissions - dispersion - deposition - policy_effects
    """
    
    def __init__(
        self,
        initial_pm25: float = None,
        initial_pm10: float = None,
    ):
        self.emission_manager = get_emission_sources()
        
        # Initialize pollution levels
        self.pm25 = initial_pm25 if initial_pm25 is not None else BASELINE_PM["pm25"]
        self.pm10 = initial_pm10 if initial_pm10 is not None else BASELINE_PM["pm10"]
        
        # Track active policy effects
        self.active_effects: List[PolicyEffect] = []
        
        # Simulation state
        self.current_hour = 0
        self.current_day = 0
        
        # History for analysis
        self.history: List[PollutionState] = []
    
    def step(
        self,
        weather: WeatherCondition,
        new_policies: List[PolicyEffect] = None,
    ) -> PollutionState:
        """
        Advance simulation by one hour.
        
        Args:
            weather: Current weather conditions
            new_policies: New policy effects to apply this hour
        
        Returns:
            Current pollution state
        """
        # Add new policy effects
        if new_policies:
            self.active_effects.extend(new_policies)
        
        # Calculate emissions (with policy modifiers)
        combined_modifiers = self._get_combined_modifiers()
        emissions = self.emission_manager.get_total_emissions(
            self.current_hour % HOURS_PER_DAY,
            combined_modifiers
        )
        
        # Calculate dispersion based on weather
        dispersion_rate = weather.get_dispersion_rate()
        
        # Calculate external pollution transport
        external = weather.get_external_transport()
        
        # Calculate direct PM reductions (e.g., water spraying)
        direct_reductions = self._get_combined_direct_reductions()
        
        # Apply the core equation
        # PM(t+1) = PM(t) + emissions + external - dispersion - direct_removal
        
        self.pm25 = (
            self.pm25 
            + emissions["pm25"] 
            + external["pm25"]
            - (self.pm25 * dispersion_rate)
            - (self.pm25 * direct_reductions.get("pm25", 0))
        )
        
        self.pm10 = (
            self.pm10 
            + emissions["pm10"]
            + external["pm10"]
            - (self.pm10 * dispersion_rate)
            - (self.pm10 * direct_reductions.get("pm10", 0))
        )
        
        # Ensure non-negative and apply realistic bounds
        self.pm25 = max(10.0, min(999.0, self.pm25))
        self.pm10 = max(20.0, min(999.0, self.pm10))
        
        # Update policy effect timers
        self._update_policy_effects()
        
        # Record state
        state = PollutionState(
            pm25=self.pm25,
            pm10=self.pm10,
            hour=self.current_hour % HOURS_PER_DAY,
            day=self.current_day,
        )
        self.history.append(state)
        
        # Advance time
        self.current_hour += 1
        if self.current_hour % HOURS_PER_DAY == 0:
            self.current_day += 1
        
        return state
    
    def _get_combined_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Combine modifiers from all active policy effects."""
        combined = {}
        
        for effect in self.active_effects:
            for source, reductions in effect.get_current_modifiers().items():
                if source not in combined:
                    combined[source] = {"pm25": 0, "pm10": 0}
                
                # Stack reductions (diminishing returns)
                for pollutant, reduction in reductions.items():
                    current = combined[source][pollutant]
                    # Multiplicative stacking: new_total = 1 - (1-current)*(1-new)
                    combined[source][pollutant] = 1 - (1 - current) * (1 - reduction)
        
        return combined
    
    def _get_combined_direct_reductions(self) -> Dict[str, float]:
        """Combine direct PM reductions from all active effects."""
        combined = {"pm25": 0, "pm10": 0}
        
        for effect in self.active_effects:
            reductions = effect.get_current_direct_reduction()
            for pollutant, reduction in reductions.items():
                # Multiplicative stacking
                combined[pollutant] = 1 - (1 - combined[pollutant]) * (1 - reduction)
        
        return combined
    
    def _update_policy_effects(self):
        """Update all policy effects and remove expired ones."""
        self.active_effects = [
            effect for effect in self.active_effects 
            if effect.tick()
        ]
    
    def run_simulation(
        self,
        weather_sequence: List[WeatherCondition],
        policy_schedule: Dict[int, List[PolicyEffect]] = None,
    ) -> List[PollutionState]:
        """
        Run a full simulation.
        
        Args:
            weather_sequence: List of hourly weather conditions
            policy_schedule: Dict mapping hour -> list of policies to activate
        
        Returns:
            List of hourly pollution states
        """
        policy_schedule = policy_schedule or {}
        
        for hour_idx, weather in enumerate(weather_sequence):
            new_policies = policy_schedule.get(hour_idx, [])
            self.step(weather, new_policies)
        
        return self.history
    
    def get_summary_stats(self) -> Dict:
        """Calculate summary statistics for the simulation."""
        if not self.history:
            return {}
        
        pm25_values = [s.pm25 for s in self.history]
        pm10_values = [s.pm10 for s in self.history]
        
        return {
            "pm25": {
                "mean": np.mean(pm25_values),
                "max": np.max(pm25_values),
                "min": np.min(pm25_values),
                "std": np.std(pm25_values),
            },
            "pm10": {
                "mean": np.mean(pm10_values),
                "max": np.max(pm10_values),
                "min": np.min(pm10_values),
                "std": np.std(pm10_values),
            },
            "severe_hours": sum(1 for s in self.history if s.get_aqi_category() == "severe"),
            "very_poor_hours": sum(1 for s in self.history if s.get_aqi_category() == "very_poor"),
            "good_hours": sum(1 for s in self.history if s.get_aqi_category() == "good"),
            "total_hours": len(self.history),
        }
    
    def reset(self, initial_pm25: float = None, initial_pm10: float = None):
        """Reset the engine to initial state."""
        self.pm25 = initial_pm25 if initial_pm25 is not None else BASELINE_PM["pm25"]
        self.pm10 = initial_pm10 if initial_pm10 is not None else BASELINE_PM["pm10"]
        self.active_effects = []
        self.current_hour = 0
        self.current_day = 0
        self.history = []


def create_engine(initial_pm25: float = None, initial_pm10: float = None) -> PollutionDynamicsEngine:
    """Factory function to create a pollution engine."""
    return PollutionDynamicsEngine(initial_pm25, initial_pm10)
