"""
Base Policy Class

Abstract interface for all policy modules. Each policy must define:
- Sources affected
- Reduction magnitude
- Duration/timing
- Cost proxy
- Rebound behavior
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

from backend.pollution_engine import PolicyEffect


@dataclass
class PolicyMetadata:
    """Descriptive metadata for a policy."""
    name: str
    display_name: str
    description: str
    category: str  # "delhi", "global", "experimental"
    sources_affected: List[str]
    cost_level: str  # "low", "medium", "high"
    sustainability: str  # "temporary", "sustained", "permanent"
    economic_impact: str  # "none", "low", "medium", "high"
    effectiveness_rating: int  # 1-5
    delhi_uses: bool
    global_uses: bool


class BasePolicy(ABC):
    """
    Abstract base class for all policies.
    
    Subclasses must implement:
    - get_metadata(): Return PolicyMetadata
    - create_effect(): Create a PolicyEffect for the simulation
    """
    
    @abstractmethod
    def get_metadata(self) -> PolicyMetadata:
        """Return descriptive metadata for this policy."""
        pass
    
    @abstractmethod
    def create_effect(
        self,
        start_hour: int = 0,
        duration_hours: int = 24,
        intensity: float = 1.0,
    ) -> PolicyEffect:
        """
        Create a PolicyEffect that can be applied to the simulation.
        
        Args:
            start_hour: Hour of day to activate (0-23)
            duration_hours: How long the policy remains active
            intensity: Scaling factor (0-1) for policy strength
        
        Returns:
            PolicyEffect instance
        """
        pass
    
    def get_effectiveness_explanation(self) -> str:
        """Return human-readable explanation of why policy has its effectiveness."""
        meta = self.get_metadata()
        return f"{meta.display_name}: {meta.description}"
    
    def get_comparison_data(self) -> Dict:
        """Get data for policy comparison matrix."""
        meta = self.get_metadata()
        return {
            "name": meta.name,
            "display_name": meta.display_name,
            "delhi_uses": meta.delhi_uses,
            "global_uses": meta.global_uses,
            "effectiveness": meta.effectiveness_rating,
            "cost": meta.cost_level,
            "sustainability": meta.sustainability,
        }


class PolicyRegistry:
    """
    Registry for all available policies.
    Allows dynamic policy discovery and selection.
    """
    
    _policies: Dict[str, BasePolicy] = {}
    
    @classmethod
    def register(cls, policy: BasePolicy):
        """Register a policy in the registry."""
        meta = policy.get_metadata()
        cls._policies[meta.name] = policy
    
    @classmethod
    def get(cls, name: str) -> Optional[BasePolicy]:
        """Get a policy by name."""
        return cls._policies.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BasePolicy]:
        """Get all registered policies."""
        return cls._policies.copy()
    
    @classmethod
    def get_by_category(cls, category: str) -> List[BasePolicy]:
        """Get all policies in a category."""
        return [
            p for p in cls._policies.values()
            if p.get_metadata().category == category
        ]
    
    @classmethod
    def get_comparison_matrix(cls) -> List[Dict]:
        """Get comparison data for all policies."""
        return [p.get_comparison_data() for p in cls._policies.values()]
