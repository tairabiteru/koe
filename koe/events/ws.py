from __future__ import annotations
import typing

from .base import WebSocketRecvEvent
from ..impl.constructs.stats import Memory, CPU, FrameStats


if typing.TYPE_CHECKING:
    from ..client import Koe
    

class WebSocketClosedEvent(WebSocketRecvEvent):
    """
    Event fired whenever a websocket closes.
    
    Attributes
    ----------
    guild_id: int
        The guild for which the websocket closed.
    code: int
        The code of the close event.
    reason: str
        The reason it was closed.
    by_remote: bool
        Whether or not it was closed remotely.
    """
    def __init__(
        self,
        koe: 'Koe',
        payload
    ):
        super().__init__(koe, payload)
        self.guild_id = int(payload['guild_id'])
        self.code = payload['code']
        self.reason = payload['reason']
        self.by_remote = payload['by_remote']


class LavalinkReadyEvent(WebSocketRecvEvent):
    """
    Event fired when Lavalink is ready.
    
    Attributes
    ----------
    resumed: bool
        Whether or not lavalink was resumed.
    session_id: str
        The session ID.
    """
    def __init__(
        self,
        koe: 'Koe',
        payload
    ):
        super().__init__(koe, payload)
        
        self.resumed = self.data['resumed']
        self.session_id = self.data['session_id']


class StatisticsEvent(WebSocketRecvEvent):
    """
    A statistics event from Lavalink.
    
    Attributes
    ----------
    num_players: int
        The number of players connected to the node.
    num_playing_players: int
        The number of actively playing players connected to the node.
    uptime: int
        The uptime in milliseconds.
    memory: Memory
        The memory statistics.
    cpu: CPU
        The CPU statistics.
    frame_stats: FrameStats | None
        The frame stats, if any are available.
    """
    def __init__(
        self,
        koe: 'Koe',
        payload
    ):
        super().__init__(koe, payload)
        
        self.num_players = self.data['players']
        self.num_playing_players = self.data['playing_players']
        self.uptime = self.data['uptime']
        
        self.memory = Memory.construct(self.data['memory'])
        self.cpu = CPU.construct(self.data['cpu'])

        if self.data['frame_stats'] is not None:
            self.frame_stats = FrameStats.construct(self.data['frame_stats'])
        else:
            self.frame_stats = None