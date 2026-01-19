"""
Simulation Scenarios

Pre-defined scenarios for fair policy comparisons under identical conditions.
Each scenario specifies:
- Weather conditions
- Active policies and timing
- Baseline emissions
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from backend.data_layer import get_weather_scenario, WeatherCondition
from backend.policies.base_policy import PolicyRegistry
from backend.pollution_engine import PolicyEffect


@dataclass
class Scenario:
    """A simulation scenario configuration."""
    name: str
    display_name: str
    description: str
    weather_type: str
    policies: List[str]
    policy_schedules: Dict[str, Dict]  # policy_name -> {start_hour, repeat_daily, etc.}
    duration_days: int = 30
    
    def get_weather_sequence(self) -> List[WeatherCondition]:
        """Get weather conditions for this scenario."""
        return get_weather_scenario(self.weather_type)[:self.duration_days * 24]
    
    def get_policy_schedule(self) -> Dict[int, List[PolicyEffect]]:
        """
        Convert policy configuration to hourly schedule.
        
        Returns:
            Dict mapping simulation hour -> list of PolicyEffects to activate
        """
        schedule = {}
        
        for policy_name in self.policies:
            policy = PolicyRegistry.get(policy_name)
            if not policy:
                continue
            
            config = self.policy_schedules.get(policy_name, {})
            start_hour = config.get("start_hour", 0)
            repeat_daily = config.get("repeat_daily", False)
            duration = config.get("duration_hours", 24)
            intensity = config.get("intensity", 1.0)
            
            if repeat_daily:
                # Activate every day at the specified hour
                for day in range(self.duration_days):
                    activation_hour = day * 24 + start_hour
                    if activation_hour not in schedule:
                        schedule[activation_hour] = []
                    schedule[activation_hour].append(
                        policy.create_effect(start_hour, duration, intensity)
                    )
            else:
                # Activate once at the start
                if start_hour not in schedule:
                    schedule[start_hour] = []
                schedule[start_hour].append(
                    policy.create_effect(start_hour, duration, intensity)
                )
        
        return schedule


# Pre-defined scenarios
SCENARIOS = {
    "baseline": Scenario(
        name="baseline",
        display_name="No Intervention (Baseline)",
        description="No policies active. Shows natural pollution evolution with standard weather.",
        weather_type="default",
        policies=[],
        policy_schedules={},
    ),
    
    "delhi_current": Scenario(
        name="delhi_current",
        display_name="Current Delhi Approach",
        description="Simulates Delhi's current strategy: water spraying 3x daily, "
                   "odd-even during peak hours, GRAP stage 2 when AQI exceeds thresholds.",
        weather_type="default",
        policies=["water_spraying", "odd_even", "grap_stage2"],
        policy_schedules={
            "water_spraying": {"start_hour": 8, "repeat_daily": True, "duration_hours": 4},
            "odd_even": {"start_hour": 8, "repeat_daily": True, "duration_hours": 12},
            "grap_stage2": {"start_hour": 0, "repeat_daily": False, "duration_hours": 24 * 30},
        },
    ),
    
    "delhi_intensive": Scenario(
        name="delhi_intensive",
        display_name="Delhi Intensive Measures",
        description="All Delhi measures at full intensity: water spraying, odd-even, "
                   "construction ban, GRAP stage 4.",
        weather_type="default",
        policies=["water_spraying", "odd_even", "construction_ban", "grap_stage4"],
        policy_schedules={
            "water_spraying": {"start_hour": 6, "repeat_daily": True, "duration_hours": 4},
            "odd_even": {"start_hour": 8, "repeat_daily": True, "duration_hours": 12},
            "construction_ban": {"start_hour": 0, "repeat_daily": False, "duration_hours": 24 * 30},
            "grap_stage4": {"start_hour": 0, "repeat_daily": False, "duration_hours": 24 * 30},
        },
    ),
    
    "global_best": Scenario(
        name="global_best",
        display_name="Global Best Practices",
        description="Proven international strategies: source elimination, industrial scrubbers, "
                   "congestion pricing, low emission zones, regional coordination.",
        weather_type="default",
        policies=[
            "source_elimination", 
            "industrial_scrubbers", 
            "congestion_pricing", 
            "low_emission_zone",
            "regional_coordination"
        ],
        policy_schedules={
            "source_elimination": {"start_hour": 0, "duration_hours": 24 * 30},
            "industrial_scrubbers": {"start_hour": 0, "duration_hours": 24 * 30},
            "congestion_pricing": {"start_hour": 7, "repeat_daily": True, "duration_hours": 12},
            "low_emission_zone": {"start_hour": 0, "duration_hours": 24 * 30},
            "regional_coordination": {"start_hour": 0, "duration_hours": 24 * 30},
        },
    ),
    
    "hybrid_optimal": Scenario(
        name="hybrid_optimal",
        display_name="Optimal Hybrid Strategy",
        description="Best combination: global structural changes + targeted Delhi measures + "
                   "experimental strategies like predictive triggering.",
        weather_type="default",
        policies=[
            "source_elimination",
            "congestion_pricing",
            "regional_coordination",
            "predictive_triggering",
            "source_weighted",
        ],
        policy_schedules={
            "source_elimination": {"start_hour": 0, "duration_hours": 24 * 30},
            "congestion_pricing": {"start_hour": 7, "repeat_daily": True, "duration_hours": 12},
            "regional_coordination": {"start_hour": 0, "duration_hours": 24 * 30},
            "predictive_triggering": {"start_hour": 0, "duration_hours": 24 * 30},
            "source_weighted": {"start_hour": 0, "duration_hours": 24 * 30},
        },
    ),
    
    "experimental": Scenario(
        name="experimental",
        display_name="Experimental Strategies",
        description="New policy ideas: source-weighted targeting, night truck bans, "
                   "AQI-based pricing, predictive triggering.",
        weather_type="default",
        policies=[
            "source_weighted",
            "night_truck_ban",
            "aqi_dynamic_pricing",
            "predictive_triggering",
            "weather_aware_construction",
        ],
        policy_schedules={
            "source_weighted": {"start_hour": 0, "duration_hours": 24 * 30},
            "night_truck_ban": {"start_hour": 22, "repeat_daily": True, "duration_hours": 8},
            "aqi_dynamic_pricing": {"start_hour": 7, "repeat_daily": True, "duration_hours": 14},
            "predictive_triggering": {"start_hour": 0, "duration_hours": 24 * 30},
            "weather_aware_construction": {"start_hour": 0, "repeat_daily": True, "duration_hours": 12},
        },
    ),
    
    "water_spraying_only": Scenario(
        name="water_spraying_only",
        display_name="Water Spraying Analysis",
        description="Special focus: Daily water spraying to demonstrate temporary effect and rebound.",
        weather_type="default",
        policies=["water_spraying"],
        policy_schedules={
            "water_spraying": {"start_hour": 8, "repeat_daily": True, "duration_hours": 4},
        },
    ),
    
    "stagnant_weather": Scenario(
        name="stagnant_weather",
        display_name="Worst Weather Conditions",
        description="Stress test: policies under worst-case weather (low wind, inversion, high humidity).",
        weather_type="stagnant",
        policies=["grap_stage4", "construction_ban"],
        policy_schedules={
            "grap_stage4": {"start_hour": 0, "duration_hours": 24 * 30},
            "construction_ban": {"start_hour": 0, "duration_hours": 24 * 30},
        },
    ),
}


def get_scenario(name: str) -> Optional[Scenario]:
    """Get a scenario by name."""
    return SCENARIOS.get(name)


def get_all_scenarios() -> Dict[str, Scenario]:
    """Get all available scenarios."""
    return SCENARIOS.copy()


def get_scenario_list() -> List[Dict]:
    """Get scenario list for API response."""
    return [
        {
            "name": s.name,
            "display_name": s.display_name,
            "description": s.description,
            "policies": s.policies,
        }
        for s in SCENARIOS.values()
    ]
