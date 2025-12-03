from collections import deque
import hikari
import typing

from .session.base import Session
from .impl.rest import RestAPI
from .impl.ws import WebSocket
from .events.ws import StatisticsEvent, LavalinkReadyEvent
from .const import __version__
from .errors import NoSessionError, ExistingSessionError
from .utils import AsyncConditionalLock, ensure_one_of
from .impl.constructs.track import Track
from .impl.constructs.player import Player
from .log import logger


if typing.TYPE_CHECKING:
    from .session.base import Session


class Koe:
    def __init__(
        self,
        bot: hikari.GatewayBot,
        host="localhost",
        port=2333,
        password="",
        ssl=False
    ):
        self.bot = bot
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        
        self._session_id: str | None = None
        self._sessions: dict[hikari.Snowflake, Session] = {}
        self._session_lock = AsyncConditionalLock()
        
        self.stats: deque['StatisticsEvent'] = deque()
        
        self._ws: WebSocket | None = None
        self._rest: RestAPI | None = None
        
        self.bot.subscribe(hikari.ShardReadyEvent, self.on_ready)
        self.bot.subscribe(LavalinkReadyEvent, self.on_lavalink_ready)
        self.bot.subscribe(StatisticsEvent, self.on_statistics)
    
    @property
    def ready(self) -> bool:
        if self._session_id is None:
            return False
        return True
    
    @property
    def rest(self) -> RestAPI:
        if self._rest is None:
            raise RuntimeError("RestAPI not ready.")
        return self._rest
    
    @property
    def bot_id(self) -> hikari.Snowflake:
        bot = self.bot.get_me()
        assert bot is not None
        return bot.id
    
    async def get_session_by(
        self,
        guild_id: hikari.Snowflake | None = None,
        voice_id: hikari.Snowflake | None = None,
        unsafe=False
    ) -> 'Session':
        ensure_one_of(guild_id=guild_id, voice_id=voice_id)
        
        async with self._session_lock(unsafe=unsafe):
            if guild_id is not None:
                session = self._sessions.get(guild_id, None)
                if session is None:
                    raise NoSessionError(guild_id=guild_id)
                return session
            
            for session in self._sessions.values():
                if voice_id == session.voice_id:
                    return session
            
            raise NoSessionError(voice_id=voice_id)
    
    async def add_session(self, session: 'Session') -> None:
        async with self._session_lock:
            existing_session = self._sessions.get(session.guild_id, None)
            if existing_session is not None:
                raise ExistingSessionError(existing_session, session.guild_id, session.voice_id)
            self._sessions[session.guild_id] = session
            logger.info(f"Added session with GID {session.guild_id}")
    
    async def rm_session(self, guild_id: hikari.Snowflake) -> 'Session':
        async with self._session_lock:
            session = self._sessions.pop(guild_id, None)
            if session is None:
                raise NoSessionError(guild_id)
            logger.info(f"Removed session with GID {session.guild_id}")
            return session
    
    async def get_session_or_none_by(
        self,
        guild_id: hikari.Snowflake | None = None,
        voice_id: hikari.Snowflake | None = None,
        unsafe=False
    ) -> Session | None:
        async with self._session_lock(unsafe=unsafe):
            try:
                return await self.get_session_by(guild_id=guild_id, voice_id=voice_id, unsafe=True)
            except NoSessionError:
                return None
    
    async def update_player(self, guild_id: hikari.Snowflake, no_replace: bool=False, data: dict={}) -> Player:
        no_replace_str = 'true' if no_replace else 'false'
        response = await self.rest.patch(
            f"sessions/{self._session_id}/players/{guild_id}",
            params={"noReplace": no_replace_str},
            payload=data
        )
        return Player.construct(response)
    
    async def get_player(self, guild_id: hikari.Snowflake) -> Player:
        player_data = await self.rest.get(
            f"sessions/{self._session_id}/players/{guild_id}",
            payload={}
        )
        return Player.construct(player_data)
    
    async def delete_player(self, guild_id: hikari.Snowflake) -> None:
        await self.rest.delete(
            f"sessions/{self._session_id}/players/{guild_id}"
        )
    
    async def load_tracks(self, identifier: str) -> Track | list[Track] | None:
        track_data = await self.rest.get("loadtracks", params={'identifier': identifier})

        load_type = track_data['load_type']
        
        if load_type == "track":
            return Track.construct(track_data['data'])
        elif load_type == "playlist":
            raise ValueError("Playlists unsupported.")
        elif load_type == "search":
            return list([Track.construct(data) for data in track_data['data']])
        elif load_type == "empty":
            return None
        else:
            return None
                    
    async def on_ready(self, _: hikari.ShardReadyEvent):
        bot_user = self.bot.get_me()
        
        if bot_user is None:
            raise RuntimeError("Bot not ready.")
        
        self._ws = WebSocket(
            bot_user.id,
            url=self.host,
            port=self.port,
            password=self.password
        )
        
        self._rest = RestAPI(
            url=self.host,
            port=self.port,
            password=self.password
        )
        
        self._ws.start(self)
        logger.info("Initialization complete.")
    
    async def on_statistics(self, event: StatisticsEvent):
        self.stats.append(event)
    
    async def on_lavalink_ready(self, event: LavalinkReadyEvent):
        self._session_id = event.session_id