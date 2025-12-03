from dataclasses import dataclass
from typing import Any, Self

from .base import Serializable
from .track import Track


@dataclass
class PlayerState(Serializable):
    time: int
    position: int
    connected: bool
    ping: int


@dataclass
class VoiceState(Serializable):
    token: str
    endpoint: str
    session_id: str


@dataclass
class Player(Serializable):
    guild_id: int
    volume: int
    paused: bool
    
    state: PlayerState
    voice: VoiceState
    track: Track | None
    
    @classmethod
    def construct(cls, data: dict[str, Any]) -> Self:
        # Lavalink transmits guild_id as a str, but no.
        data['guild_id'] = int(data['guild_id'])
        return super().construct(data)