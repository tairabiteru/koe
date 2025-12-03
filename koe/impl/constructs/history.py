from dataclasses import dataclass
import hikari

from .base import Serializable


@dataclass
class HistoryRecord(Serializable):
    time: float
    actor_id: int | None
    action: str
    
    def get_actor(self, bot: hikari.GatewayBot) -> hikari.User | None:
        if self.actor_id is None:
            return None
        return bot.cache.get_user(self.actor_id)
    
    def __repr__(self) -> str:
        return f"<Action {self.action} by {self.actor_id}>"