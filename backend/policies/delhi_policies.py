"""
Delhi Government Policy Modules

Implementation of current Delhi government measures:
- Water Spraying / Anti-smog guns
- Odd-Even Scheme
- Construction Bans
- GRAP (Graded Response Action Plan)
"""

from typing import Dict, Optional
import math

from backend.policies.base_policy import BasePolicy, PolicyMetadata, PolicyRegistry
from backend.pollution_engine import PolicyEffect
from backend.config import WATER_SPRAYING, ODD_EVEN, CONSTRUCTION_BAN, GRAP


class WaterSprayingPolicy(BasePolicy):
    """
    Water Spraying / Anti-smog guns
    
    Effect: Temporarily settles airborne dust particles
    - Strong effect on PM10 (15% reduction)
    - Weak effect on PM2.5 (5% reduction) - particles too fine
    - Effect decays rapidly (4-hour half-life)
    - No cumulative benefit
    - High water usage
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="water_spraying",
            display_name="Water Spraying",
            description="Anti-smog guns and water tankers spray water to settle dust. "
                       "Effect is temporary (4 hours) and mainly affects larger PM10 particles. "
                       "PM2.5 particles are too fine to be effectively captured.",
            category="delhi",
            sources_affected=["airborne_dust"],
            cost_level="medium",
            sustainability="temporary",
            economic_impact="none",
            effectiveness_rating=1,  # Very low
            delhi_uses=True,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 4,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        # Water spraying directly reduces ambient PM, doesn't affect sources
        return PolicyEffect(
            policy_name="water_spraying",
            source_modifiers={},  # No source reduction
            direct_pm_reduction={
                "pm25": WATER_SPRAYING["pm25_reduction"] * intensity,
                "pm10": WATER_SPRAYING["pm10_reduction"] * intensity,
            },
            hours_remaining=duration_hours,
            decay_rate=1.0 / WATER_SPRAYING["decay_hours"],  # Exponential decay
            initial_strength=1.0,
            current_strength=1.0,
        )
    
    def get_effectiveness_explanation(self) -> str:
        return (
            "Water spraying causes a temporary 10-15% dip in PM10 readings, "
            "but the effect decays within 4 hours. PM2.5 (the more harmful pollutant) "
            "sees only 5% reduction. Meanwhile, emission sources continue unchanged, "
            "causing rapid rebound. Analysis shows: 30 days of water spraying ≈ "
            "1 day of banning diesel trucks in terms of net pollution reduction."
        )


class OddEvenPolicy(BasePolicy):
    """
    Odd-Even Vehicle Scheme
    
    Effect: Restricts private vehicles based on license plate
    - Affects only private cars (~12% of vehicle emissions)
    - Real compliance around 70%
    - Two-wheelers and commercial vehicles exempt
    - Temporary (active only during scheme days)
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="odd_even",
            display_name="Odd-Even Scheme",
            description="Private cars with odd/even license plates drive on alternate days. "
                       "Only affects ~12% of total vehicle emissions. Two-wheelers, women drivers, "
                       "and commercial vehicles are exempt, limiting effectiveness.",
            category="delhi",
            sources_affected=["vehicles"],
            cost_level="low",
            sustainability="temporary",
            economic_impact="medium",
            effectiveness_rating=2,
            delhi_uses=True,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 8,
        duration_hours: int = 12,  # 8 AM - 8 PM
        intensity: float = 1.0,
    ) -> PolicyEffect:
        effective_reduction = ODD_EVEN["effective_reduction"] * intensity
        
        return PolicyEffect(
            policy_name="odd_even",
            source_modifiers={
                "vehicles": {
                    "pm25": effective_reduction,
                    "pm10": effective_reduction,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,  # No decay while active
            initial_strength=1.0,
            current_strength=1.0,
        )


class ConstructionBanPolicy(BasePolicy):
    """
    Construction Ban
    
    Effect: Halts all construction activities
    - Strong reduction in construction dust (35% PM10, 20% PM25)
    - High economic impact (job losses, project delays)
    - Temporary measure during emergencies
    """
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name="construction_ban",
            display_name="Construction Ban",
            description="Complete halt on construction activities in Delhi. "
                       "Effective at reducing construction dust but causes significant "
                       "economic disruption and job losses.",
            category="delhi",
            sources_affected=["construction"],
            cost_level="low",  # Direct cost low, indirect high
            sustainability="temporary",
            economic_impact="high",
            effectiveness_rating=3,
            delhi_uses=True,
            global_uses=False,  # Rare globally
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        return PolicyEffect(
            policy_name="construction_ban",
            source_modifiers={
                "construction": {
                    "pm25": CONSTRUCTION_BAN["pm25_reduction"] * intensity,
                    "pm10": CONSTRUCTION_BAN["pm10_reduction"] * intensity,
                }
            },
            direct_pm_reduction={},
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


class GRAPPolicy(BasePolicy):
    """
    GRAP - Graded Response Action Plan
    
    Effect: Multi-stage emergency response based on AQI levels
    - Stage 1 (Poor): Basic dust control
    - Stage 2 (Very Poor): Construction restrictions
    - Stage 3 (Severe): Vehicle restrictions
    - Stage 4 (Emergency): School closures, WFH
    
    Reactive rather than proactive - acts after pollution rises
    """
    
    def __init__(self, stage: int = 1):
        self.stage = min(4, max(1, stage))
    
    def get_metadata(self) -> PolicyMetadata:
        return PolicyMetadata(
            name=f"grap_stage{self.stage}",
            display_name=f"GRAP Stage {self.stage}",
            description=f"Graded Response Action Plan Stage {self.stage}. "
                       f"Reactive emergency measures triggered by AQI thresholds. "
                       f"Actions: {', '.join(GRAP[f'stage{self.stage}']['actions'])}",
            category="delhi",
            sources_affected=["vehicles", "construction", "industry"],
            cost_level="medium" if self.stage < 3 else "high",
            sustainability="temporary",
            economic_impact="low" if self.stage < 3 else "high",
            effectiveness_rating=self.stage,  # Higher stages more effective
            delhi_uses=True,
            global_uses=False,
        )
    
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        stage_data = GRAP[f"stage{self.stage}"]
        effectiveness = stage_data["effectiveness"] * intensity
        
        # GRAP affects multiple sources depending on stage
        source_modifiers = {}
        
        if self.stage >= 1:
            source_modifiers["construction"] = {"pm25": effectiveness * 0.5, "pm10": effectiveness * 0.7}
        if self.stage >= 2:
            source_modifiers["vehicles"] = {"pm25": effectiveness * 0.3, "pm10": effectiveness * 0.3}
        if self.stage >= 3:
            source_modifiers["industry"] = {"pm25": effectiveness * 0.4, "pm10": effectiveness * 0.4}
        if self.stage >= 4:
            source_modifiers["domestic"] = {"pm25": effectiveness * 0.2, "pm10": effectiveness * 0.2}
        
        return PolicyEffect(
            policy_name=f"grap_stage{self.stage}",
            source_modifiers=source_modifiers,
            direct_pm_reduction={
                "pm25": effectiveness * 0.1,  # Some direct effect from dust control
                "pm10": effectiveness * 0.15,
            },
            hours_remaining=duration_hours,
            decay_rate=0,
            initial_strength=1.0,
            current_strength=1.0,
        )


# Register all Delhi policies
def register_delhi_policies():
    """Register all Delhi government policies."""
    PolicyRegistry.register(WaterSprayingPolicy())
    PolicyRegistry.register(OddEvenPolicy())
    PolicyRegistry.register(ConstructionBanPolicy())
    PolicyRegistry.register(GRAPPolicy(1))
    PolicyRegistry.register(GRAPPolicy(2))
    PolicyRegistry.register(GRAPPolicy(3))
    PolicyRegistry.register(GRAPPolicy(4))


# Auto-register on import
register_delhi_policies()
