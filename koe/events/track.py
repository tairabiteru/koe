import typing

from .ws import WebSocketRecvEvent
from ..impl.constructs.track import Track, TrackException


if typing.TYPE_CHECKING:
    from ..client import Koe


class TrackEvent(WebSocketRecvEvent):
    """
    A base track event.
    
    Attributes
    ----------
    track: Track
        The track associated with the event.
    """
    def __init__(self, koe: 'Koe', payload: dict):
        super().__init__(koe, payload)
        self.track = Track.construct(payload['track'])


class TrackStartEvent(TrackEvent):
    """
    Event fired whenever a track starts.
    
    Attributes
    ----------
    track: Track
        The track that started.
    guild_id: int
        The guild in which playback started.
    """
    def __init__(self, koe: 'Koe', payload: dict):
        super().__init__(koe, payload)
        self.guild_id: int = payload['guild_id']


class TrackEndEvent(TrackEvent):
    """
    Event fired whenever a track ends.
    
    Attributes
    ----------
    track: Track
        The track that ended.
    reason: str
        The reason the track ended.
    """
    def __init__(self, koe: 'Koe', payload: dict):
        super().__init__(koe, payload)
        self.reason: str = payload['reason']
    
    @property
    def may_start_next(self) -> bool:
        return self.reason in ['finished', 'loadFailed']
        

class TrackExceptionEvent(TrackEvent):
    """
    Event fired whenever a track exception occurs.
    
    Attributes
    ----------
    track: Track
        The track that threw the exception.
    exception: TrackException
        The exception that occurred.
    """
    def __init__(self, koe: 'Koe', payload: dict):
        super().__init__(koe, payload)
        self.exception: TrackException = TrackException.construct(payload['exception'])