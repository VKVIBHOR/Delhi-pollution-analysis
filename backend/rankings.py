"""
Policy Rankings

Score and rank policies by multiple criteria:
- Pollution reduction (weighted)
- Cost efficiency
- Sustainability
- Economic impact
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

from backend.policies.base_policy import PolicyRegistry
from backend.simulator import Simulator


@dataclass
class PolicyScore:
    """Scoring for a single policy."""
    name: str
    display_name: str
    category: str
    
    # Individual scores (0-10)
    pollution_score: float  # Based on PM2.5 reduction
    cost_score: float  # Inverse of cost
    sustainability_score: float  # Permanent > sustained > temporary
    economic_impact_score: float  # Lower impact = higher score
    
    # Computed
    overall_score: float = 0.0
    rank: int = 0
    
    def compute_overall(
        self,
        pollution_weight: float = 0.4,
        cost_weight: float = 0.2,
        sustainability_weight: float = 0.25,
        economic_weight: float = 0.15,
    ):
        """Compute weighted overall score."""
        self.overall_score = (
            self.pollution_score * pollution_weight +
            self.cost_score * cost_weight +
            self.sustainability_score * sustainability_weight +
            self.economic_impact_score * economic_weight
        )
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category,
            "pollution_score": round(self.pollution_score, 1),
            "cost_score": round(self.cost_score, 1),
            "sustainability_score": round(self.sustainability_score, 1),
            "economic_impact_score": round(self.economic_impact_score, 1),
            "overall_score": round(self.overall_score, 1),
            "rank": self.rank,
        }


class PolicyRanker:
    """Ranks policies by multiple criteria."""
    
    # Mapping from metadata strings to scores
    COST_SCORES = {"low": 9, "medium": 5, "high": 2}
    SUSTAINABILITY_SCORES = {"temporary": 2, "sustained": 7, "permanent": 10}
    ECONOMIC_IMPACT_SCORES = {"none": 10, "low": 8, "medium": 5, "high": 2}
    EFFECTIVENESS_TO_POLLUTION = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}  # 1-5 rating to 0-10 score
    
    def __init__(self):
        self.scores: List[PolicyScore] = []
    
    def compute_all_scores(self) -> List[PolicyScore]:
        """Compute scores for all registered policies."""
        self.scores = []
        
        for name, policy in PolicyRegistry.get_all().items():
            meta = policy.get_metadata()
            
            score = PolicyScore(
                name=meta.name,
                display_name=meta.display_name,
                category=meta.category,
                pollution_score=self.EFFECTIVENESS_TO_POLLUTION.get(meta.effectiveness_rating, 5),
                cost_score=self.COST_SCORES.get(meta.cost_level, 5),
                sustainability_score=self.SUSTAINABILITY_SCORES.get(meta.sustainability, 5),
                economic_impact_score=self.ECONOMIC_IMPACT_SCORES.get(meta.economic_impact, 5),
            )
            score.compute_overall()
            self.scores.append(score)
        
        # Sort and assign ranks
        self.scores.sort(key=lambda x: x.overall_score, reverse=True)
        for i, score in enumerate(self.scores):
            score.rank = i + 1
        
        return self.scores
    
    def get_rankings(self) -> List[Dict]:
        """Get rankings as list of dicts for API response."""
        if not self.scores:
            self.compute_all_scores()
        return [s.to_dict() for s in self.scores]
    
    def get_rankings_by_category(self) -> Dict[str, List[Dict]]:
        """Get rankings grouped by category."""
        if not self.scores:
            self.compute_all_scores()
        
        by_category = {"delhi": [], "global": [], "experimental": []}
        for score in self.scores:
            if score.category in by_category:
                by_category[score.category].append(score.to_dict())
        
        return by_category
    
    def get_comparison_matrix(self) -> List[Dict]:
        """
        Get the hard-coded policy comparison matrix.
        This is the key truth table from requirements.
        """
        return [
            {
                "measure": "Water Spraying",
                "delhi_uses": "✅ Yes",
                "global_uses": "❌ No",
                "effectiveness": "🔴 Very Low",
                "why": "Temporary, no source reduction, rapid rebound"
            },
            {
                "measure": "Blanket Bans",
                "delhi_uses": "✅ Yes",
                "global_uses": "🟡 Rare",
                "effectiveness": "🟡 Medium",
                "why": "High economic cost, temporary, non-targeted"
            },
            {
                "measure": "Source Elimination",
                "delhi_uses": "🟡 Limited",
                "global_uses": "✅ Yes",
                "effectiveness": "🟢 High",
                "why": "Permanent, addresses root cause"
            },
            {
                "measure": "Economic Penalties",
                "delhi_uses": "🔴 Weak",
                "global_uses": "✅ Strong",
                "effectiveness": "🟢 High",
                "why": "Market-based, sustained behavior change"
            },
            {
                "measure": "Predictive Triggers",
                "delhi_uses": "🟡 Partial (forecast-based GRAP since 2024)",
                "global_uses": "✅ Yes",
                "effectiveness": "🟢 High",
                "why": "Proactive, prevents buildup"
            },
        ]
    
    def get_top_recommendations(self, n: int = 5) -> List[Dict]:
        """Get top N policy recommendations."""
        if not self.scores:
            self.compute_all_scores()
        
        recommendations = []
        for score in self.scores[:n]:
            policy = PolicyRegistry.get(score.name)
            meta = policy.get_metadata()
            
            recommendations.append({
                "rank": score.rank,
                "name": score.display_name,
                "category": score.category,
                "overall_score": round(score.overall_score, 1),
                "description": meta.description,
                "key_benefit": self._get_key_benefit(score),
            })
        
        return recommendations
    
    def _get_key_benefit(self, score: PolicyScore) -> str:
        """Generate key benefit statement for a policy."""
        benefits = []
        
        if score.pollution_score >= 8:
            benefits.append("high pollution reduction")
        if score.cost_score >= 8:
            benefits.append("low cost")
        if score.sustainability_score >= 8:
            benefits.append("permanent effect")
        if score.economic_impact_score >= 8:
            benefits.append("minimal economic disruption")
        
        if not benefits:
            return "moderate across all factors"
        return ", ".join(benefits)


def create_ranker() -> PolicyRanker:
    """Factory function."""
    return PolicyRanker()
