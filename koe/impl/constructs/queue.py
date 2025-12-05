from .track import Track
from ...errors import InvalidPosition
from ...utils import AsyncConditionalLock


class Queue:
    def __init__(self):
        self._queue = []
        self._pos = 0
        self.lock = AsyncConditionalLock()
    
    def __repr__(self) -> str:
        return f"<Queue pos: {self._pos}, len: {len(self._queue)}>"
    
    async def insert(self, track: Track, position: int, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            self._queue.insert(position, track)
    
    async def append(self, track: Track, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            self._queue.append(track)
    
    async def prepend(self, track: Track, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            self._queue.insert(self._pos+1, track)
    
    async def is_empty(self, unsafe: bool=False) -> bool:
        async with self.lock(unsafe=unsafe):
            return self._queue == []
    
    async def reset(self, unsafe: bool=False) -> None:
        async with self.lock(unsafe=unsafe):
            self._queue = []
            self._pos = 0
    
    async def get_pos(self, unsafe: bool=False) -> int:
        async with self.lock(unsafe=unsafe):
            return self._pos
    
    async def advance_by(self, by: int, unsafe: bool=False) -> Track:
        async with self.lock(unsafe=unsafe):
            if by == 0:
                raise InvalidPosition("The queue cannot be advanced by 0.")
            
            new_pos = self._pos + by
            if new_pos < 0 or new_pos >= len(self._queue):
                lwr_bnd = -(self._pos) if self._pos != 0 else 1
                upr_bnd = len(self._queue) - (self._pos + 1) if (self._pos + 1) != len(self._queue) else -1
                
                if lwr_bnd == upr_bnd:
                    raise InvalidPosition(f"Invalid advance: `{by}`. The queue can currently only be advanced by `{lwr_bnd}`.")
                raise InvalidPosition(f"Invalid advance: `{by}`. The queue can currently only be advanced by values between `{lwr_bnd}` and `{upr_bnd}`.")

            self._pos = new_pos
            return self._queue[self._pos]
    
    async def advance_to(self, to: int, zero_indexed: bool=False, unsafe: bool=False) -> Track:
        to = to - 1 if zero_indexed is False else to
        
        if to < 0 or to > len(self._queue) - 1:
            if zero_indexed is True:
                raise InvalidPosition(f"Invalid advance: `{to}`. The queue can currently only be advanced to alues between `0` and `{len(self._queue)-1}`.")
            raise InvalidPosition(f"Invalid advance: `{to+1}`. The queue can currently only be advanced to values between `1` and `{len(self._queue)}`.")

        if to == self._pos:
            if zero_indexed is True:
                raise InvalidPosition(f"`{to}` is the current position of the queue. This operation would have no effect.")
            raise InvalidPosition(f"`{to+1}` is the current position of the queue. This operation would have no effect.")
        self._pos = to
        return self._queue[self._pos]
        
    async def advance(self, unsafe: bool=False) -> Track | None:
        async with self.lock(unsafe=unsafe):
            try:
                return await self.advance_by(1, unsafe=True)
            except InvalidPosition:
                return None
    
    async def insert_after_current(self, track: Track, unsafe: bool=False) -> None:
        await self.insert(track, self._pos + 1)
    
    async def get_current(self, unsafe: bool=False) -> Track | None:
        async with self.lock(unsafe=unsafe):
            try:
                return self._queue[self._pos]
            except IndexError:
                return None
    
    async def remove_at(self, pos: int, unsafe=True) -> Track:
        if (pos - 1) == self._pos:
            raise InvalidPosition(f"Invalid position: `{pos}`. Removing at the current position is not allowed.")
        
        try:
            return self._queue.pop(pos-1)
        except IndexError:
            raise InvalidPosition(f"Invalid position: `{pos}`. Values must be between `1` and `{len(self._queue)}`.")
    
    async def get_all_and_pos(self, unsafe: bool=False) -> tuple[list[Track], int]:
        async with self.lock(unsafe=unsafe):
            return self._queue, self._pos