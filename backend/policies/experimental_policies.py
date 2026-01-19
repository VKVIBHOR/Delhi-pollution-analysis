"""
Experimental Policy Modules

Implementation of new/proposed pollution control strategies:
- Source-weighted intervention (target top emitters)
- Night truck ban
- Weather-aware construction scheduling
- AQI-based dynamic congestion pricing
- Predictive triggering
"""

from typing import Dict

from backend.policies.base_policy import BasePolicy, PolicyMetadata, PolicyRegistry
from backend.pollution_engine import PolicyEffect
from backend.config import EXPERIMENTAL_POLICIES


class SourceWeightedPolicy(BasePolicy):
    """
    Source-Weighted Intervention
    
    Strategy: Target top 20% of emitters instead of blanket restrictions
    - Higher effectiveness per unit of enforcement
    - Lower economic disruption
    - Data-driven approach
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="source_weighted",
            display_name="Source-Weighted Targeting",
            description="Instead of blanket restrictions, identify and target the top 20% "
                       "of polluters (oldest vehicles, specific factories, hotspot areas). "
                       "More effective and less disruptive than uniform policies.",
            category="experimental",
            sources_affected=["vehicles", "industry"],
            cost_level="medium",
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=4,
            delhi_uses=False,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 30,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = EXPERIMENTAL_POLICIES["source_weighted"]
        
        return PolicyEffect(
            policy_name="source_weighted",
            source_modifiers={
                "vehicles": {
                    "pm25": data["pm25_reduction"] * intensity * 0.6,
                    "pm10": data["pm10_reduction"] * intensity * 0.6,
                },
                "industry": {
                    "pm25": data["pm25_reduction"] * intensity * 0.4,
                    "pm10": data["pm10_reduction"] * intensity * 0.4,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


class NightTruckBanPolicy(BasePolicy):
    """
    Night Truck Ban
    
    Strategy: Ban heavy trucks from 10 PM - 6 AM in city limits
    - Trucks contribute disproportionately to emissions
    - Night entry currently used to avoid daytime traffic
    - Forces logistics shift but cleaner nights
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="night_truck_ban",
            display_name="Night Truck Ban",
            description="Ban heavy commercial vehicles from city limits 10 PM - 6 AM. "
                       "Diesel trucks are major PM emitters. Alternative: mandate "
                       "cleaner vehicles for night entry.",
            category="experimental",
            sources_affected=["vehicles"],
            cost_level="low",
            sustainability="sustained",
            economic_impact="medium",
            effectiveness_rating=3,
            delhi_uses=False,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 22,  # 10 PM
        duration_hours: int = 8,  # Until 6 AM
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = EXPERIMENTAL_POLICIES["night_truck_ban"]
        
        return PolicyEffect(
            policy_name="night_truck_ban",
            source_modifiers={
                "vehicles": {
                    "pm25": data["pm25_reduction"] * intensity,
                    "pm10": data["pm10_reduction"] * intensity,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


class WeatherAwareConstructionPolicy(BasePolicy):
    """
    Weather-Aware Construction Scheduling
    
    Strategy: Halt construction during temperature inversions
    - Inversions trap pollution near ground
    - Construction dust makes it worse
    - Smart scheduling, not blanket bans
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="weather_aware_construction",
            display_name="Weather-Aware Construction",
            description="Halt construction activities when weather conditions "
                       "(temperature inversions, low wind) would trap pollutants. "
                       "Smarter than blanket bans - less economic disruption.",
            category="experimental",
            sources_affected=["construction"],
            cost_level="low",
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=3,
            delhi_uses=False,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 12,  # Typically inversions in morning
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = EXPERIMENTAL_POLICIES["weather_aware_construction"]
        
        return PolicyEffect(
            policy_name="weather_aware_construction",
            source_modifiers={
                "construction": {
                    "pm25": data["pm25_reduction"] * intensity,
                    "pm10": data["pm10_reduction"] * intensity,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


class AQIDynamicPricingPolicy(BasePolicy):
    """
    AQI-Based Dynamic Congestion Pricing
    
    Strategy: Vehicle entry fees scale with real-time AQI
    - Higher fees during poor AQI = fewer vehicles
    - Revenue positive
    - Behavioral nudge + direct reduction
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="aqi_dynamic_pricing",
            display_name="AQI-Based Dynamic Pricing",
            description="Vehicle entry fees that increase with AQI levels. "
                       "₹50 for good AQI, ₹500 for severe. Creates strong incentive "
                       "to reduce driving when pollution is worst.",
            category="experimental",
            sources_affected=["vehicles"],
            cost_level="low",  # Revenue generating
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=4,
            delhi_uses=False,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 7,
        duration_hours: int = 14,  # 7 AM - 9 PM
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = EXPERIMENTAL_POLICIES["aqi_dynamic_pricing"]
        
        return PolicyEffect(
            policy_name="aqi_dynamic_pricing",
            source_modifiers={
                "vehicles": {
                    "pm25": data["pm25_reduction"] * intensity,
                    "pm10": data["pm10_reduction"] * intensity,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


class PredictiveTriggeringPolicy(BasePolicy):
    """
    Predictive Triggering
    
    Strategy: Act 3-5 days before predicted smog episodes
    - Use weather forecasts to predict inversions
    - Pre-emptive restrictions before pollution builds
    - More effective than reactive GRAP
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="predictive_triggering",
            display_name="Predictive Triggering",
            description="Use weather forecasts to predict smog episodes 3-5 days ahead. "
                       "Activate restrictions BEFORE pollution builds up, not after. "
                       "Much more effective than reactive GRAP.",
            category="experimental",
            sources_affected=["vehicles", "construction", "industry"],
            cost_level="low",
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=5,
            delhi_uses=False,
            global_uses=True,  # Used in some cities
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 5,  # 5 days of pre-emptive action
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = EXPERIMENTAL_POLICIES["predictive_triggering"]
        
        # Affects multiple sources with moderate restrictions
        return PolicyEffect(
            policy_name="predictive_triggering",
            source_modifiers={
                "vehicles": {
                    "pm25": data["pm25_reduction"] * intensity * 0.4,
                    "pm10": data["pm10_reduction"] * intensity * 0.4,
                },
                "construction": {
                    "pm25": data["pm25_reduction"] * intensity * 0.3,
                    "pm10": data["pm10_reduction"] * intensity * 0.4,
                },
                "industry": {
                    "pm25": data["pm25_reduction"] * intensity * 0.3,
                    "pm10": data["pm10_reduction"] * intensity * 0.2,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


# Register all experimental policies
def register_experimental_policies():
    """Register all experimental policies."""
    PolicyRegistry.register(SourceWeightedPolicy())
    PolicyRegistry.register(NightTruckBanPolicy())
    PolicyRegistry.register(WeatherAwareConstructionPolicy())
    PolicyRegistry.register(AQIDynamicPricingPolicy())
    PolicyRegistry.register(PredictiveTriggeringPolicy())


# Auto-register on import
register_experimental_policies()
