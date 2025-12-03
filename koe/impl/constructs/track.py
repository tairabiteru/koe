from __future__ import annotations
from dataclasses import dataclass

from .base import Serializable


@dataclass
class TrackInfo(Serializable):
    identifier: str
    is_seekable: bool
    author: str
    length: int
    is_stream: bool
    position: int
    title: str
    uri: str | None
    artwork_url: str | None
    irsc: str | None
    source_name: str


@dataclass
class TrackException(Serializable):
    message: str
    severity: str
    cause: str
    cause_stack_trace: str


@dataclass
class Track(Serializable):
    encoded: str
    info: TrackInfo
    plugin_info: dict
    user_data: dict