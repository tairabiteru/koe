from dataclasses import dataclass

from .base import Serializable


@dataclass
class Memory(Serializable):
    free: int
    used: int
    allocated: int
    reservable: int


@dataclass
class CPU(Serializable):
    cores: int
    system_load: float
    lavalink_load: float


@dataclass
class FrameStats(Serializable):
    sent: int
    nulled: int
    deficit: int