"""
Global Benchmark Policy Modules

Implementation of proven international pollution control strategies:
- Source Elimination (industry relocation/closure)
- Industrial Scrubbers (emission control equipment)
- Congestion Pricing
- Low Emission Zones (LEZ)
- Regional Coordination
"""

from typing import Dict

from backend.policies.base_policy import BasePolicy, PolicyMetadata, PolicyRegistry
from backend.pollution_engine import PolicyEffect
from backend.config import GLOBAL_POLICIES


class SourceEliminationPolicy(BasePolicy):
    """
    Source Elimination
    
    Strategy: Relocate or close polluting industries
    - Largest assumed effect in the model (45-50% cut in affected emissions)
    - Permanent solution
    - High implementation cost and time
    - Proven in Beijing, London (post-industrial transition)
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="source_elimination",
            display_name="Source Elimination",
            description="Permanently relocate or close major polluting industries. "
                       "Most effective long-term strategy. Requires political will and "
                       "economic transition planning. Successfully used in Beijing's "
                       "industrial relocation program.",
            category="global",
            sources_affected=["industry"],
            cost_level="high",
            sustainability="permanent",
            economic_impact="high",
            effectiveness_rating=5,
            delhi_uses=False,  # Limited
            global_uses=True,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 30,  # Permanent, but simulate 30 days
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = GLOBAL_POLICIES["source_elimination"]
        
        return PolicyEffect(
            policy_name="source_elimination",
            source_modifiers={
                "industry": {
                    "pm25": data["pm25_reduction"] * intensity,
                    "pm10": data["pm10_reduction"] * intensity,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,  # No decay - permanent
            initial_strength=1.0,
            current_strength=1.0,
        )


class IndustrialScrubbersPolicy(BasePolicy):
    """
    Industrial Scrubbers
    
    Strategy: Mandate emission control equipment on factories
    - High effectiveness (30-50% reduction from industry)
    - Permanent solution
    - Initial capital cost, then sustained
    - Standard in EU, US, China (recent)
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="industrial_scrubbers",
            display_name="Industrial Scrubbers",
            description="Mandate installation of air pollution control equipment "
                       "(scrubbers, filters, electrostatic precipitators) in all industries. "
                       "Reduces industrial emissions by 30-50% permanently.",
            category="global",
            sources_affected=["industry"],
            cost_level="high",
            sustainability="permanent",
            economic_impact="medium",
            effectiveness_rating=5,
            delhi_uses=False,
            global_uses=True,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 30,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = GLOBAL_POLICIES["industrial_scrubbers"]
        
        return PolicyEffect(
            policy_name="industrial_scrubbers",
            source_modifiers={
                "industry": {
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


class CongestionPricingPolicy(BasePolicy):
    """
    Congestion Pricing
    
    Strategy: Dynamic vehicle entry fees based on traffic/AQI
    - Medium-high effectiveness (25% vehicle emission reduction)
    - Sustained effect (behavioral change)
    - Revenue positive (funds public transit)
    - Proven in London, Singapore, Stockholm
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="congestion_pricing",
            display_name="Congestion Pricing",
            description="Charge vehicles to enter city center during peak hours. "
                       "Fees can be dynamic based on AQI levels. Revenue funds public "
                       "transit improvements. Successfully reduced traffic 30% in London.",
            category="global",
            sources_affected=["vehicles"],
            cost_level="low",  # Actually generates revenue
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=4,
            delhi_uses=False,
            global_uses=True,
        )
    
    def create_effect(
        self,
        start_hour: int = 7,
        duration_hours: int = 12,  # Daytime only
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = GLOBAL_POLICIES["congestion_pricing"]
        
        return PolicyEffect(
            policy_name="congestion_pricing",
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


class LowEmissionZonePolicy(BasePolicy):
    """
    Low Emission Zones (LEZ)
    
    Strategy: Ban high-polluting vehicles from core areas
    - Medium-high effectiveness
    - Sustained (permanent infrastructure)
    - Encourages fleet modernization
    - Standard in EU cities
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="low_emission_zone",
            display_name="Low Emission Zones",
            description="Designate city center as low emission zone. Only vehicles "
                       "meeting emission standards (BS-VI or equivalent) allowed entry. "
                       "Accelerates transition to cleaner vehicles.",
            category="global",
            sources_affected=["vehicles"],
            cost_level="medium",
            sustainability="sustained",
            economic_impact="medium",
            effectiveness_rating=4,
            delhi_uses=False,
            global_uses=True,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 30,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = GLOBAL_POLICIES["low_emission_zones"]
        
        return PolicyEffect(
            policy_name="low_emission_zone",
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


class RegionalCoordinationPolicy(BasePolicy):
    """
    Regional Coordination
    
    Strategy: Coordinate pollution control across NCR region
    - Addresses external pollution (crop burning, neighboring industries)
    - High effectiveness for regional pollutants
    - Delhi alone can't control 30-40% of its pollution
    - Requires interstate cooperation
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="regional_coordination",
            display_name="Regional Coordination",
            description="Coordinate pollution control with Haryana, Punjab, UP (NCR). "
                       "Critical for addressing crop burning (40% of winter pollution) "
                       "and industrial pollution from satellite cities.",
            category="global",
            sources_affected=["external"],
            cost_level="medium",
            sustainability="sustained",
            economic_impact="low",
            effectiveness_rating=5,
            delhi_uses=False,
            global_uses=True,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24 * 30,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        data = GLOBAL_POLICIES["regional_coordination"]
        
        return PolicyEffect(
            policy_name="regional_coordination",
            source_modifiers={
                "external": {
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


# Register all global policies
def register_global_policies():
    """Register all global benchmark policies."""
    PolicyRegistry.register(SourceEliminationPolicy())
    PolicyRegistry.register(IndustrialScrubbersPolicy())
    PolicyRegistry.register(CongestionPricingPolicy())
    PolicyRegistry.register(LowEmissionZonePolicy())
    PolicyRegistry.register(RegionalCoordinationPolicy())


# Auto-register on import
register_global_policies()
