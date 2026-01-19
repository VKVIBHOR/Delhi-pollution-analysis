"""
Insights Generator

Generates human-readable explanations of simulation results.
Explains WHY policies work or don't work.
"""

from typing import Dict, List, Optional
from backend.simulator import SimulationResult, Simulator
from backend.scenarios import get_scenario
from backend.policies.base_policy import PolicyRegistry


class InsightsGenerator:
    """Generates natural language insights from simulation results."""
    
    def __init__(self, simulator: Simulator):
        self.simulator = simulator
    
    def generate_scenario_insight(self, result: SimulationResult) -> str:
        """Generate insight for a single scenario."""
        scenario = get_scenario(result.scenario_name)
        scenario_name = scenario.display_name if scenario else result.scenario_name
        
        pm25_mean = result.stats["pm25"]["mean"]
        pm25_max = result.stats["pm25"]["max"]
        severe_hours = result.stats["severe_hours"]
        good_hours = result.stats["good_hours"]
        total_hours = result.stats["total_hours"]
        
        severe_pct = severe_hours / total_hours * 100
        good_pct = good_hours / total_hours * 100
        
        insight = f"**{scenario_name}**: "
        
        if pm25_mean > 250:
            insight += f"Average PM2.5 of {pm25_mean:.0f} µg/m³ remains in 'Very Poor' category. "
        elif pm25_mean > 120:
            insight += f"Average PM2.5 of {pm25_mean:.0f} µg/m³ in 'Poor' category. "
        elif pm25_mean > 60:
            insight += f"Average PM2.5 of {pm25_mean:.0f} µg/m³ in 'Moderate' category. "
        else:
            insight += f"Average PM2.5 of {pm25_mean:.0f} µg/m³ achieves 'Satisfactory' or better. "
        
        if severe_pct > 10:
            insight += f"Severe air quality persisted for {severe_pct:.0f}% of the period. "
        
        if good_pct > 20:
            insight += f"Good air quality achieved {good_pct:.0f}% of the time. "
        
        return insight
    
    def generate_comparison_insights(
        self,
        comparison_data: Dict,
    ) -> List[str]:
        """Generate insights comparing multiple scenarios."""
        insights = []
        comparisons = comparison_data["comparisons"]
        
        if len(comparisons) < 2:
            return ["Need at least 2 scenarios to compare."]
        
        # Find best and worst
        best = comparisons[0]  # Already sorted by reduction
        worst = comparisons[-1]
        
        # Overall comparison
        insights.append(
            f"**Best performer**: {best['display_name']} achieved {best['pm25_reduction_pct']:.1f}% "
            f"PM2.5 reduction compared to baseline."
        )
        
        if worst['pm25_reduction_pct'] < 10:
            insights.append(
                f"**Least effective**: {worst['display_name']} achieved only "
                f"{worst['pm25_reduction_pct']:.1f}% reduction, suggesting cosmetic rather than "
                f"structural intervention."
            )
        
        # Specific policy comparisons
        delhi_result = next((c for c in comparisons if c["scenario"] == "delhi_current"), None)
        global_result = next((c for c in comparisons if c["scenario"] == "global_best"), None)
        
        if delhi_result and global_result:
            diff = global_result["pm25_reduction_pct"] - delhi_result["pm25_reduction_pct"]
            if diff > 10:
                insights.append(
                    f"**Key finding**: Global best practices outperform current Delhi approach by "
                    f"{diff:.1f} percentage points. This gap represents the difference between "
                    f"addressing symptoms vs. causes."
                )
        
        # Water spraying specific insight
        if any(c["scenario"] == "water_spraying_only" for c in comparisons):
            water = next(c for c in comparisons if c["scenario"] == "water_spraying_only")
            insights.append(
                f"**Water spraying reality**: Only {water['pm25_reduction_pct']:.1f}% reduction over 30 days. "
                f"Effect decays within hours while emission sources continue. "
                f"30 days of water spraying ≈ 1 day of truck ban in net impact."
            )
        
        return insights
    
    def generate_policy_explanation(self, policy_name: str) -> str:
        """Generate explanation for why a policy is effective or not."""
        policy = PolicyRegistry.get(policy_name)
        if not policy:
            return f"Unknown policy: {policy_name}"
        
        return policy.get_effectiveness_explanation()
    
    def generate_water_spraying_deep_dive(self) -> Dict:
        """
        Special deep-dive on water spraying effectiveness.
        This is a key insight the app must communicate.
        """
        return {
            "title": "Water Spraying: A Closer Look",
            "sections": [
                {
                    "heading": "How It Works",
                    "content": "Anti-smog guns and water tankers spray water to settle airborne "
                              "dust particles. The water droplets collide with suspended particles, "
                              "making them heavier and causing them to fall."
                },
                {
                    "heading": "The Limitation",
                    "content": "This only affects particles already in the air (PM10 > PM2.5). "
                              "It does nothing to reduce emission sources. The effect decays "
                              "exponentially - within 4 hours, new emissions replace settled particles."
                },
                {
                    "heading": "The Numbers",
                    "content": "Initial PM10 reduction: 15%. Initial PM2.5 reduction: 5% (particles too fine). "
                              "After 4 hours: <2% residual effect. After 8 hours: Pollution back to baseline."
                },
                {
                    "heading": "The Comparison",
                    "content": "30 days of 3x daily water spraying = 1 day of banning diesel trucks. "
                              "Water used: 150,000 liters/day. Cost: ~₹45,000/day. "
                              "Net PM2.5 improvement: ~2-3%."
                },
                {
                    "heading": "Why It Persists",
                    "content": "Water spraying is visible, immediate, and creates a perception of action. "
                              "It's politically convenient - shows 'something is being done' without "
                              "addressing difficult structural issues like vehicle emissions or industry."
                },
                {
                    "heading": "What Would Work Instead",
                    "content": "Same resources spent on: (1) Subsidizing electric vehicles, "
                              "(2) Industrial emission controls, (3) Regional crop burning solutions. "
                              "Each would provide 10-50x more pollution reduction per rupee spent."
                }
            ],
            "key_insight": "Water spraying is a cosmetic measure that addresses symptoms, not causes. "
                          "It creates temporary relief while avoiding the harder work of emission reduction."
        }
    
    def generate_full_report(
        self,
        scenario_names: List[str] = None,
    ) -> Dict:
        """
        Generate a complete simulation report with all insights.
        
        Args:
            scenario_names: Scenarios to include, or None for default set
        
        Returns:
            Complete report with data and insights
        """
        if scenario_names is None:
            scenario_names = [
                "baseline", 
                "delhi_current", 
                "global_best", 
                "hybrid_optimal",
                "water_spraying_only"
            ]
        
        # Run comparisons
        comparison_data = self.simulator.compare_scenarios(scenario_names)
        
        # Generate insights
        comparison_insights = self.generate_comparison_insights(comparison_data)
        
        # Individual scenario insights
        scenario_insights = []
        for name in scenario_names:
            if name in self.simulator.results:
                insight = self.generate_scenario_insight(self.simulator.results[name])
                scenario_insights.append(insight)
        
        # Water spraying deep dive
        water_analysis = self.generate_water_spraying_deep_dive()
        
        return {
            "comparison_data": comparison_data,
            "comparison_insights": comparison_insights,
            "scenario_insights": scenario_insights,
            "water_spraying_analysis": water_analysis,
            "key_conclusions": [
                "Delhi's current measures (water spraying, odd-even) provide <15% improvement",
                "Global best practices (source elimination, pricing) achieve 40-60% reduction",
                "Water spraying is cosmetic - 30 days ≈ 1 day of truck ban",
                "Targeting top 20% of emitters outperforms blanket bans",
                "Predictive triggering is more effective than reactive GRAP",
                "Regional coordination is essential - 30-40% of pollution comes from outside Delhi"
            ]
        }


def create_insights_generator(simulator: Simulator = None) -> InsightsGenerator:
    """Factory function."""
    if simulator is None:
        from backend.simulator import create_simulator
        simulator = create_simulator()
    return InsightsGenerator(simulator)
