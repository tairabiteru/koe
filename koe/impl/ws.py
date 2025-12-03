import asyncio
import hikari
import orjson as json
import typing
import websockets

from .connection import Connection
from ..events.ws import LavalinkReadyEvent, StatisticsEvent, WebSocketClosedEvent, WebSocketRecvEvent
from ..events.player import PlayerUpdateEvent
from ..events.track import TrackStartEvent, TrackEndEvent
from ..const import __version__
from ..utils import lavalink_dictovert
from ..log import logger


if typing.TYPE_CHECKING:
    from ..client import Koe


class WebSocket(Connection):
    def __init__(
        self,
        user_id: hikari.Snowflake,
        client_identifier: str = f"Koe v{__version__}",
        protocol: str="ws", 
        url: str="localhost", 
        port: int=80, 
        password: str=""
    ):
        self.user_id = user_id
        self.client_identifier = client_identifier
        self.protocol =  protocol
        self.url = url
        self.port = port
        self.password = password
        
        self._connected: bool = False
    
    @property
    def headers(self) -> dict[str, str]:
        return {
            'Authorization': self.password,
            'User-Id': str(self.user_id),
            'Client-Name': self.client_identifier
        }
        
    async def _loop(self, koe: 'Koe') -> None:
        async with websockets.connect(f"{self.route}/v4/websocket", additional_headers=self.headers) as ws:
            self._connected = True
            
            async for message in ws:
                data = json.loads(message)
                data = lavalink_dictovert(data)
                
                if data['op'] == "ready":
                    event = LavalinkReadyEvent(koe, data)
                    
                elif data['op'] == "stats":
                    event = StatisticsEvent(koe, data)
                
                elif data['op'] == 'playerUpdate':
                    event = PlayerUpdateEvent(koe, data)
                    
                elif data['op'] == 'event':
                    event = self.handle_ws_event(koe, data)
                else:
                    print(f"Unknown event type {data}")
                    continue

                koe.bot.event_manager.dispatch(event)
    
    def handle_ws_event(self, koe: 'Koe', data: dict[str, typing.Any]) -> WebSocketRecvEvent:
        if data['type'] == 'WebSocketClosedEvent':
            event = WebSocketClosedEvent(koe, data)
        elif data['type'] == 'TrackStartEvent':
            event = TrackStartEvent(koe, data)
        elif data['type'] == 'TrackEndEvent':
            event = TrackEndEvent(koe, data)
        else:
            raise ValueError(f"Unknown event {data}")
        return event
    
    def start(self, koe: 'Koe') -> None:
        if self._connected is True:
            raise RuntimeError("Websocket loop is already connected.")
        
        loop = asyncio.get_event_loop()
        logger.info(f"Starting websocket connection to {self.route}/v4/websocket")
        loop.create_task(self._loop(koe))
                