from __future__ import annotations
from collections.abc import Callable
import hikari
import typing

from ..utils import AsyncConditionalLock, ensure_one_of
from ..impl.constructs.track import Track
from ..impl.constructs.player import PlayerState
from ..impl.constructs.queue import Queue
from ..events.player import PlayerUpdateEvent
from ..events.track import TrackStartEvent, TrackEndEvent
from ..errors import UninitializedSessionError, NoSessionError, ExistingSessionError


if typing.TYPE_CHECKING:
    from ..client import Koe


def require_connected(func: Callable) -> Callable:
    async def inner(session: Session, *args, **kwargs):
        if session._connected is False:
            raise NoSessionError(guild_id=session.guild_id)
        return await func(session, *args, **kwargs)
    return inner


class Session:
    def __init__(self, koe: 'Koe'):
        self.koe = koe
        
        self._guild_id: hikari.Snowflake | None = None
        self._voice_id: hikari.Snowflake | None = None
        self._channel_id: hikari.Snowflake | None = None
        self._id: str | None = None
        
        self.lock = AsyncConditionalLock()
        self.queue = Queue()
        
        self._connected: bool = False
        self._volume: int = 100
        self._player_state: PlayerState | None = None
        self._paused: bool | None = None
        self._is_playing: bool = False
        self._current_track: Track | None = None
        self._current_track_pos: int | None = None
    
    @property
    def bot(self) -> hikari.GatewayBot:
        return self.koe.bot
    
    @property
    def guild_id(self) -> hikari.Snowflake:
        if self._guild_id is None:
            raise UninitializedSessionError
        return self._guild_id

    @property
    def voice_id(self) -> hikari.Snowflake:
        if self._voice_id is None:
            raise UninitializedSessionError
        return self._voice_id
    
    @property
    def channel_id(self) -> hikari.Snowflake:
        if self._channel_id is None:
            raise RuntimeError("Channel ID was not set for this session.")
        return self._channel_id
        
    async def set_channel_id(self, channel_id: hikari.Snowflake) -> None:
        async with self.lock:
            self._channel_id = channel_id
    
    @property
    def exists(self) -> bool:
        return self._connected

    async def on_voice_state_update(self, event: hikari.VoiceStateUpdateEvent) -> None:
        # If the user is not the bot, we don't care.
        if event.state.user_id != self.koe.bot_id:
            return
        
        # A disconnect happened.
        if event.state.channel_id is None:
            try:
                await self.koe.rm_session(self.guild_id)
                return
            except NoSessionError:
                return

        if event.guild_id == self.guild_id:
            async with self.lock:                
                # If not, the channel must have updated.
                self._guild_id = event.guild_id
                self._id = event.state.session_id
                self._voice_id = event.state.channel_id
    
    async def on_voice_server_update(self, event: hikari.VoiceServerUpdateEvent) -> None:
        async with self.lock:
            if event.guild_id != self.guild_id:
                return
            
            assert event.endpoint is not None
        
            player = await self.koe.update_player(
                guild_id=event.guild_id,
                data={
                    'voice': {
                        'token': event.token,
                        'sessionId': self._id,
                        'endpoint': event.endpoint.replace("wss://", "")
                    }
                }
            )
            
            self._state = player.state
    
    async def on_track_start(self, event: TrackStartEvent) -> None:
        async with self.lock:
            self._is_playing = True
            self._current_track = event.track
    
    async def on_track_end(self, event: TrackEndEvent) -> None:
        async with self.lock:
            self._is_playing = False
            self._current_track = None
            self._current_track_pos = None

            if event.reason in ['finished', 'loadFailed']:
                track = await self.queue.advance()
            elif event.reason == "stopped":
                return
            else:
                track = await self.queue.get_current()
            
            if track is None:
                return
            
            try:
                await self.play(track, replace=False, unsafe=True)
            except NoSessionError:
                pass
    
    async def on_player_update(self, event: PlayerUpdateEvent) -> None:
        if event.guild_id != self.guild_id:
            return
        
        async with self.lock:
            self._current_track_pos = event.state.position
            
    def subscribe(self) -> None:
        self.bot.subscribe(hikari.VoiceStateUpdateEvent, self.on_voice_state_update)
        self.bot.subscribe(hikari.VoiceServerUpdateEvent, self.on_voice_server_update)
        self.bot.subscribe(PlayerUpdateEvent, self.on_player_update)
        self.bot.subscribe(TrackStartEvent, self.on_track_start)
        self.bot.subscribe(TrackEndEvent, self.on_track_end)
        self.bot.subscribe(PlayerUpdateEvent, self.on_player_update)
    
    def unsubscribe(self) -> None:
        self.bot.unsubscribe(hikari.VoiceStateUpdateEvent, self.on_voice_state_update)
        self.bot.unsubscribe(hikari.VoiceServerUpdateEvent, self.on_voice_server_update)
        self.bot.unsubscribe(PlayerUpdateEvent, self.on_player_update)
        self.bot.unsubscribe(TrackStartEvent, self.on_track_start)
        self.bot.unsubscribe(TrackEndEvent, self.on_track_end)
        self.bot.unsubscribe(PlayerUpdateEvent, self.on_player_update)
        
    async def connect(
        self,
        guild_id: hikari.Snowflake,
        voice_id: hikari.Snowflake,
        channel_id: hikari.Snowflake | None = None
    ) -> None:
        async with self.lock:
            try:
                self._connected = True
                self._guild_id = guild_id
                self._voice_id = voice_id
                self._channel_id = channel_id
                await self.koe.add_session(self)
                await self.koe.update_player(guild_id)
                await self.bot.update_voice_state(guild_id, voice_id)
                self.subscribe()
            except ExistingSessionError:
                self._connected = False
                self._guild_id = None
                self._voice_id = None
                self._channel_id = None
                raise
    
    async def disconnect(self) -> None:
        async with self.lock:
            self._connected = False
            await self.koe.delete_player(self.guild_id)
            await self.bot.update_voice_state(self.guild_id, None)
    
            try:
                await self.koe.rm_session(self.guild_id)
            except NoSessionError:
                pass
            
            self.unsubscribe()
    
    @require_connected
    async def _set_volume(self, level: int) -> None:
        await self.koe.update_player(
            self.guild_id,
            no_replace=True,
            data={
                'volume': level
            }
        )
        self._volume = level
    
    async def set_volume(self, level: int, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            self._volume = level
            await self._set_volume(self._volume)
    
    async def incr_volume(self, level: int, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            if self._volume is None:
                raise RuntimeError("Volume is null.")
            level = self._volume + level
            await self._set_volume(level)
    
    @require_connected
    async def stop(self, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            await self.koe.update_player(
                self.guild_id,
                no_replace=False,
                data={
                    'track': {
                        'encoded': None
                    }
                }
            )
    
    @require_connected
    async def skip(self, to: int | None=None, by: int | None=None, unsafe: bool=False) -> None:
        ensure_one_of(to=to, by=by)
        async with self.lock(unsafe=unsafe):
            if to is not None:
                track = await self.queue.advance_to(to)
            else:
                assert by is not None
                track = await self.queue.advance_by(by)
            
            await self.play(track, replace=True, unsafe=True)
    
    @require_connected
    async def play(self, track: Track, replace: bool=True, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            await self.koe.update_player(
                self.guild_id,
                no_replace=not replace,
                data={
                    'track': {
                        'encoded': track.encoded
                    }
                }
            )
    
    @require_connected
    async def seek(self, hours: int=0, minutes: int=0, seconds: int=0, millis: int=0, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            pos = (hours * 3600) * 1000
            pos += (minutes * 60) * 1000
            pos += seconds * 1000
            pos += millis
            
            assert self._current_track is not None
            if millis > self._current_track.info.length:
                raise ValueError("The time entered is longer than the current track.")
                        
            await self.koe.update_player(
                self.guild_id,
                no_replace=True,
                data={
                    'position': millis
                }
            )
    
    @require_connected
    async def set_pause(self, state: bool, unsafe: bool=False) -> bool:
        async with self.lock(unsafe=unsafe):
            if self._paused == state:
                return False
            
            await self.koe.update_player(
                self.guild_id,
                no_replace=True,
                data={
                    'paused': state
                }
            )
            self._paused = state
            return True
    
    @require_connected
    async def toggle_pause(self, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            await self.set_pause(not self._paused, unsafe=True)
    
    @require_connected
    async def enqueue(self, track: Track, begin_playback: bool=True):
        async with self.lock:
            await self.queue.append(track)
            
            if not self._is_playing and begin_playback is True:
                next_track = await self.queue.advance()
                
                if next_track is None:
                    next_track = track
                    
                assert next_track is not None
                await self.play(next_track, unsafe=True)