import typing

from .ws import WebSocketRecvEvent
from ..impl.constructs.player import PlayerState


if typing.TYPE_CHECKING:
    from ..client import Koe


class PlayerUpdateEvent(WebSocketRecvEvent):
    """
    A player update event recieved from Lavalink.
    
    Attributes
    ----------
    guild_id: int
        The ID of the guild where the player is active.
    state: PlayerState
        The state of the player.
    """
    def __init__(self, koe: 'Koe', payload: dict):
        super().__init__(koe, payload)
        self.guild_id = int(payload['guild_id'])
        self.state = PlayerState.construct(payload['state'])