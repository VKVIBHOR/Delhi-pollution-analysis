"""
Main Simulator

Orchestrates simulations and generates comparative analysis.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.pollution_engine import PollutionDynamicsEngine, PollutionState, create_engine
from backend.scenarios import Scenario, get_scenario, get_all_scenarios, SCENARIOS
from backend.data_layer import get_weather_scenario
from backend.policies.base_policy import PolicyRegistry

# Import policies to register them
from backend.policies import delhi_policies, global_policies, experimental_policies


class SimulationResult:
    """Results from a single simulation run."""
    
    def __init__(
        self,
        scenario_name: str,
        history: List[PollutionState],
        stats: Dict,
    ):
        self.scenario_name = scenario_name
        self.history = history
        self.stats = stats
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "scenario": self.scenario_name,
            "history": [s.to_dict() for s in self.history],
            "stats": {
                "pm25": {k: round(v, 2) for k, v in self.stats["pm25"].items()},
                "pm10": {k: round(v, 2) for k, v in self.stats["pm10"].items()},
                "severe_hours": self.stats["severe_hours"],
                "very_poor_hours": self.stats["very_poor_hours"],
                "good_hours": self.stats["good_hours"],
                "total_hours": self.stats["total_hours"],
            },
        }
    
    def get_time_series(self, pollutant: str = "pm25") -> List[float]:
        """Get time series data for a pollutant."""
        if pollutant == "pm25":
            return [s.pm25 for s in self.history]
        else:
            return [s.pm10 for s in self.history]


class Simulator:
    """Main simulation orchestrator."""
    
    def __init__(self):
        self.results: Dict[str, SimulationResult] = {}
    
    def run_scenario(
        self,
        scenario_name: str,
        duration_days: int = 30,
    ) -> SimulationResult:
        """
        Run a single scenario simulation.
        
        Args:
            scenario_name: Name of pre-defined scenario or "custom"
            duration_days: Length of simulation
        
        Returns:
            SimulationResult object
        """
        scenario = get_scenario(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        # Create fresh engine
        engine = create_engine()
        
        # Get weather and policy schedules
        weather_sequence = scenario.get_weather_sequence()
        policy_schedule = scenario.get_policy_schedule()
        
        # Run simulation
        history = engine.run_simulation(weather_sequence, policy_schedule)
        stats = engine.get_summary_stats()
        
        result = SimulationResult(scenario_name, history, stats)
        self.results[scenario_name] = result
        
        return result
    
    def run_custom_scenario(
        self,
        policies: List[str],
        weather_type: str = "default",
        duration_days: int = 30,
    ) -> SimulationResult:
        """
        Run a custom simulation with selected policies.
        
        Args:
            policies: List of policy names to activate
            weather_type: Weather scenario type
            duration_days: Simulation duration
        
        Returns:
            SimulationResult object
        """
        # Create temporary scenario
        scenario = Scenario(
            name="custom",
            display_name="Custom Scenario",
            description="User-defined policy combination",
            weather_type=weather_type,
            policies=policies,
            policy_schedules={
                p: {"start_hour": 0, "repeat_daily": True, "duration_hours": 24}
                for p in policies
            },
            duration_days=duration_days,
        )
        
        engine = create_engine()
        weather_sequence = scenario.get_weather_sequence()
        policy_schedule = scenario.get_policy_schedule()
        
        history = engine.run_simulation(weather_sequence, policy_schedule)
        stats = engine.get_summary_stats()
        
        result = SimulationResult("custom", history, stats)
        self.results["custom"] = result
        
        return result
    
    def run_comparison(
        self,
        scenario_names: List[str] = None,
    ) -> Dict[str, SimulationResult]:
        """
        Run multiple scenarios for comparison.
        
        Args:
            scenario_names: List of scenario names, or None for default set
        
        Returns:
            Dict of scenario_name -> SimulationResult
        """
        if scenario_names is None:
            scenario_names = ["baseline", "delhi_current", "global_best", "hybrid_optimal"]
        
        results = {}
        for name in scenario_names:
            results[name] = self.run_scenario(name)
        
        return results
    
    def compare_scenarios(
        self,
        scenario_names: List[str],
    ) -> Dict:
        """
        Generate comparative analysis of scenarios.
        
        Args:
            scenario_names: Scenarios to compare
        
        Returns:
            Comparison data including rankings
        """
        results = self.run_comparison(scenario_names)
        
        # Calculate improvement over baseline
        baseline = results.get("baseline")
        if not baseline:
            # Run baseline if not included
            baseline = self.run_scenario("baseline")
        
        baseline_pm25 = baseline.stats["pm25"]["mean"]
        baseline_pm10 = baseline.stats["pm10"]["mean"]
        
        comparisons = []
        for name, result in results.items():
            pm25_reduction = (baseline_pm25 - result.stats["pm25"]["mean"]) / baseline_pm25 * 100
            pm10_reduction = (baseline_pm10 - result.stats["pm10"]["mean"]) / baseline_pm10 * 100
            
            scenario = get_scenario(name)
            
            comparisons.append({
                "scenario": name,
                "display_name": scenario.display_name if scenario else name,
                "pm25_mean": result.stats["pm25"]["mean"],
                "pm10_mean": result.stats["pm10"]["mean"],
                "pm25_reduction_pct": round(pm25_reduction, 1),
                "pm10_reduction_pct": round(pm10_reduction, 1),
                "severe_hours": result.stats["severe_hours"],
                "good_hours": result.stats["good_hours"],
            })
        
        # Rank by PM2.5 reduction
        comparisons.sort(key=lambda x: x["pm25_reduction_pct"], reverse=True)
        for i, c in enumerate(comparisons):
            c["rank"] = i + 1
        
        return {
            "baseline_pm25": baseline_pm25,
            "baseline_pm10": baseline_pm10,
            "comparisons": comparisons,
        }


def run_water_spraying_analysis() -> Dict:
    """
    Special analysis demonstrating water spraying ineffectiveness.
    
    Returns:
        Detailed comparison data
    """
    simulator = Simulator()
    
    # Run baseline and water spraying scenarios
    baseline = simulator.run_scenario("baseline")
    water = simulator.run_scenario("water_spraying_only")
    
    # Calculate the equivalence
    # How many days of water spraying = 1 day of truck ban?
    water_pm25_daily_reduction = (baseline.stats["pm25"]["mean"] - water.stats["pm25"]["mean"]) / 30
    
    # Estimate truck ban effect (from night_truck_ban policy)
    truck_ban_daily_reduction = baseline.stats["pm25"]["mean"] * 0.18  # 18% reduction
    
    equivalence_ratio = truck_ban_daily_reduction / max(water_pm25_daily_reduction, 0.1)
    
    return {
        "baseline_pm25_mean": round(baseline.stats["pm25"]["mean"], 2),
        "water_spraying_pm25_mean": round(water.stats["pm25"]["mean"], 2),
        "daily_pm25_reduction": round(water_pm25_daily_reduction, 2),
        "truck_ban_daily_reduction": round(truck_ban_daily_reduction, 2),
        "equivalence": f"{int(equivalence_ratio)} days of water spraying ≈ 1 day of truck ban",
        "conclusion": "Water spraying provides minimal sustained benefit. The effect decays within hours "
                     "while emission sources continue unabated, causing rapid rebound.",
    }


# Convenience function for API
def create_simulator() -> Simulator:
    """Factory function to create a simulator."""
    return Simulator()
