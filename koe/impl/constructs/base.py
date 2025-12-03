from __future__ import annotations
import typing as t
from dacite import from_dict

from ...utils import lavalink_dictovert


class Serializable:
    """
    A serializable object.
    
    This class bases a lot of classes which are ultimately dataclass
    representations of JSON information. It provides a classmethod
    which allows for an easy way to convert Lavalink's JSON into nice
    clean objects.
    """
    @classmethod
    def construct(cls, data: dict[str, t.Any]) -> t.Self:
        """
        Construct an instance of a dataclass from the data.

        Arguments
        ---------
        data: dict[str, t.Any]
            The dictionary to be converted.

        Returns
        -------
        t.Self
            The constructed dataclass.
        """
        data = lavalink_dictovert(data)
        return from_dict(cls, data)