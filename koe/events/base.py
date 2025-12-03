from __future__ import annotations
import abc
import hikari
import typing


if typing.TYPE_CHECKING:
    from ..client import Koe


class KoeEvent(hikari.Event, abc.ABC):
    """
    Base Koe event.
    
    Attributes
    ----------
    app: hikari.RESTAware
        The application associated with Koe.
    koe: Koe
        The Koe client.
    """
    def __init__(self, koe: 'Koe'):
        self._app = koe.bot
        self.koe = koe
    
    @property
    def app(self) -> hikari.RESTAware:
        return self._app


class WebSocketRecvEvent(KoeEvent):
    """
    Base event for any websocket recieve event.
    
    Attributes
    ----------
    koe: Koe
        The Koe client.
    data: dict[str, typing.Any]
        The data recieved from the websocket.
    """
    def __init__(
        self,
        koe: 'Koe',
        data: dict[str, typing.Any]
    ):  
        super().__init__(koe)
        self.data = data