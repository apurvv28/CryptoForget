import random
from typing import Any, Dict, List, Optional

from faker import Faker

from src.unlearning.sisa import hash_user_to_shard

fake = Faker()
fake.seed_instance(42)

DEFAULT_CANDIDATE_NEWS = [
    "N10001", "N10002", "N10003", "N10004", "N10005",
    "N10006", "N10007", "N10008", "N10009", "N10010"
]

CATEGORIES = ["finance", "technology", "sports", "entertainment", "health", "science"]


class UserAgent:
    """Represents an individual virtual user agent interacting with the recommendation system."""

    def __init__(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> None:
        self.user_id = user_id
        self.name = name or fake.name()
        self.email = email or fake.email()
        self.category_preference = random.choice(CATEGORIES)
        self.shard_id = hash_user_to_shard(user_id)
        self.consent_status = True
        self.is_unlearned = False
        self.click_history: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "category_preference": self.category_preference,
            "shard_id": self.shard_id,
            "consent_status": self.consent_status,
            "is_unlearned": self.is_unlearned,
            "click_count": len(self.click_history),
        }


class UserAgentPopulationManager:
    """Manages a virtual population of 15-20 simulated user agents."""

    def __init__(self, population_size: int = 20) -> None:
        self.population_size = population_size
        self.agents: Dict[str, UserAgent] = {}
        self._initialize_population()

    def _initialize_population(self) -> None:
        """Initializes 20 synthetic user agents mapped to MIND user IDs (U1000 to U1019)."""
        for i in range(self.population_size):
            user_id = f"U{1000 + i}"
            agent = UserAgent(user_id=user_id)
            # Give initial synthetic click history
            agent.click_history = [f"N{random.randint(10000, 20000)}" for _ in range(3)]
            self.agents[user_id] = agent

    def list_agents(self) -> List[Dict[str, Any]]:
        """Returns list of all active simulated user agents."""
        return [agent.to_dict() for agent in self.agents.values()]

    def get_agent(self, user_id: str) -> Optional[UserAgent]:
        """Returns agent by user_id."""
        return self.agents.get(user_id)

    def add_agent(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> UserAgent:
        """Onboards a new simulated user agent."""
        agent = UserAgent(user_id=user_id, name=name, email=email)
        self.agents[user_id] = agent
        return agent

    def record_click(self, user_id: str, news_id: str) -> int:
        """Records a click event for a simulated user agent."""
        agent = self.get_agent(user_id)
        if agent:
            agent.click_history.append(news_id)
            return len(agent.click_history)
        return 1

    def mark_unlearned(self, user_id: str) -> None:
        """Marks user agent as unlearned / deleted."""
        agent = self.get_agent(user_id)
        if agent:
            agent.consent_status = False
            agent.is_unlearned = True
            agent.click_history = []

    def reset_all_agents(self) -> None:
        """Restores consent status and undoes deletion state for all virtual user agents."""
        for agent in self.agents.values():
            agent.consent_status = True
            agent.is_unlearned = False
            if not agent.click_history:
                agent.click_history = [f"N{random.randint(10000, 20000)}" for _ in range(3)]


# Singleton population manager
_agent_manager_instance = None


def get_agent_manager() -> UserAgentPopulationManager:
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = UserAgentPopulationManager()
    return _agent_manager_instance
