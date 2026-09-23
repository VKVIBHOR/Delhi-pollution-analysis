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
                f"**Water spraying reality**: Only {water['pm25_reduction_pct']:.1f}% PM2.5 reduction over 30 days. "
                f"The effect decays within hours while emission sources continue."
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
                    "content": "Model assumptions: 15% initial PM10 reduction and 5% initial PM2.5 reduction "
                              "(fine particles are harder to wash out), decaying over about 4 hours. "
                              "Simulated over 30 days of daily spraying, average PM10 falls by about 11% "
                              "and PM2.5 by about 4%."
                },
                {
                    "heading": "The Comparison",
                    "content": "Under identical weather, packages that cut emissions at source "
                              "(industry controls, pricing, low-emission zones, regional coordination) "
                              "reduce simulated average PM2.5 by roughly 27-32%, several times more than "
                              "spraying alone. Real-world evidence is also limited: a 2025 CEEW review "
                              "found little evidence that anti-smog guns work at scale."
                },
                {
                    "heading": "Why It Persists",
                    "content": "Water spraying is visible and immediate, so it signals action quickly. "
                              "Around 68% of National Clean Air Programme funds have gone to road-dust "
                              "management (CREA, 2026), compared with much smaller shares for transport "
                              "and industry."
                },
                {
                    "heading": "What Would Work Instead",
                    "content": "Shift resources toward measures that reduce emissions at source: "
                              "(1) clean public transport and vehicle electrification, "
                              "(2) industrial emission controls, (3) region-wide action on crop and "
                              "biomass burning. Evaluate any dust measure with before-and-after monitoring."
                }
            ],
            "key_insight": "Water spraying treats pollution already in the air, not what produces it. "
                          "It gives short-lived relief; lasting gains come from cutting emissions at source."
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
                "Delhi's current mix (daily spraying, odd-even, GRAP Stage II) lowers simulated 30-day average PM2.5 by about 15%",
                "Source-based packages (industry controls, pricing, regional coordination) lower it by about 27-32%",
                "Daily water spraying alone lowers PM2.5 by about 4% (PM10 by about 11%); the effect fades within hours",
                "Weather can outweigh policy: under stagnant conditions, even GRAP IV plus a construction ban leaves PM2.5 far above the normal-weather baseline",
                "Acting on forecasts before smog builds matters; Delhi's GRAP has allowed forecast-based invocation since its 2024 revision",
                "All results depend on assumed effect sizes and are relative, not calibrated forecasts (see README: Limitations)"
            ]
        }


def create_insights_generator(simulator: Simulator = None) -> InsightsGenerator:
    """Factory function."""
    if simulator is None:
        from backend.simulator import create_simulator
        simulator = create_simulator()
    return InsightsGenerator(simulator)
