import hikari
import typing


if typing.TYPE_CHECKING:
    from .session.base import Session
    

class KoeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ExistingSessionError(KoeError):
    def __init__(
        self,
        existing_session: 'Session',
        guild_id: hikari.Snowflake,
        voice_id: hikari.Snowflake
    ):
        self.existing_session = existing_session
        self.guild_id = guild_id
        self.voice_id = voice_id
        
        if self.is_same_vc:
            super().__init__(f"Request to connect to VID #{self.voice_id}, but I'm already connected.")
        else:
            super().__init__(f"Request to connect to VID #{self.voice_id}, but I'm already connected in that guild to VID #{self.existing_session.voice_id}.")
    
    @property
    def is_same_vc(self) -> bool:
        return self.voice_id == self.existing_session.voice_id


class NoSessionError(KoeError):
    def __init__(
        self,
        guild_id: hikari.Snowflake | None = None,
        voice_id: hikari.Snowflake | None = None
    ):
        if all([guild_id, voice_id]):
            raise ValueError("Only one of guild_id or voice_id may be provided, not both.")
        if not any([guild_id, voice_id]):
            raise ValueError("One of guild_id or voice_id must be provided.")

        if guild_id is not None:
            super().__init__(f"Session with GID #{guild_id} does not exist.")
        else:
            super().__init__(f"Session with VID #{voice_id} does not exist.")


class VoiceRequiredError(KoeError):
    def __init__(self):
        super().__init__("User is not in a voice channel, but it is required.")
    
    
class UninitializedSessionError(KoeError):
    def __init__(self):
        super().__init__("Session is not connected.")


class InvalidPosition(KoeError):
    pass