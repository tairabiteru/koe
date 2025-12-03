import asyncio
import typing as t


class AsyncConditionalLock:
    """
    An asyncio.Lock which only locks conditionally.
    
    Ex:
    ```
    async with lock:
      # do stuff while locked
    ```
    ```
    async with lock(unsafe=True):
      # do stuff unlocked
    ```
    
    The primary purpose of this is to facilitate easy lock usage in Koe.
    Typically, when calling a function which messes with memory data, we
    want to acquire a lock to ensure thread safety. However, sometimes these
    functions are called in other functions which have already acquired the
    same lock, so in this situation we don't want to acquire the lock or else
    we enter an infinite loop. Rather than having an unsafe version and a
    safe version, we can just have one function which uses this.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._unsafe = False
    
    async def __aenter__(self):
        if self._unsafe is False:
            await self._lock.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):        
        if self._lock.locked() is True:
            self._lock.release()
            self._unsafe = False
        
        if exc_type is not None:
            raise exc_val
        return True
    
    def __call__(self, unsafe: bool=False):
        self._unsafe = unsafe
        return self


def ensure_one_of(**kwargs) -> None:
    if not any([val is not None for val in kwargs.values()]):
        raise ValueError(f"One of {', '.join(kwargs.keys())} must be passed.")
    if all(kwargs.values()):
        raise ValueError(f"Only one of {', '.join(kwargs.keys())} may be passed.")


def camel_case_to_snake_case(string: str) -> str:
    out = ""
    for char in string:
        if char.isupper():
            out += f"_{char.lower()}"
        else:
            out += char
    return out


def lavalink_dictovert(data: dict[str, t.Any]) -> dict[str, t.Any]:
    """
    Convert from lavalink dictionary format to mine.
    
    Lavalink sends camelCased keys in its JSON, but this is Python
    and I like snake_case better.

    Args:
        data (dict): The dict converted from JSON from lavalink.

    Returns:
        dict: The same dict, but with snake_case keys.
    """
    new = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = lavalink_dictovert(value)
            
        key = camel_case_to_snake_case(key)
        new[key] = value
    return new