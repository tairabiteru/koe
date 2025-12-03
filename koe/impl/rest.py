import aiohttp
import orjson as json

from .connection import Connection
from ..utils import lavalink_dictovert


class RestAPI(Connection):
    def __init__(
        self,
        url: str="localhost",
        port: int=2333,
        password: str=""
    ):
        super().__init__(
            protocol="http",
            url=url,
            port=port,
            password=password
        )
        
        self._http = aiohttp.ClientSession()
        
    @property
    def headers(self) -> dict[str, str]:
        return {
            'Authorization': self.password,
            'Content-Type': 'application/json'
        }
        
    @staticmethod
    def get_query_str(d: dict[str, str]) -> str:
        if d:
            p = []
            for key, value in d.items():
                p.append(f"{key}={value}")
            return f"?{'&'.join(p)}"
        else:
            return ""
    
    async def get(self, endpoint: str, params={}, payload={}) -> dict:
        query = self.get_query_str(params)
        response = await self._http.get(
            f"{self.route}/v4/{endpoint}{query}",
            headers=self.headers,
            data=payload
        )
        data = await response.text()
        return lavalink_dictovert(json.loads(data))

    async def patch(self, endpoint: str, params={}, payload={}) -> dict:
        query = self.get_query_str(params)
        response = await self._http.patch(
            f"{self.route}/v4/{endpoint}{query}",
            headers=self.headers,
            data=json.dumps(payload)
        )
        data = await response.text()
        return lavalink_dictovert(json.loads(data))

    async def delete(self, endpoint: str, payload={}) -> dict:
        response = await self._http.delete(
            f"{self.route}/v4/{endpoint}",
            headers=self.headers,
            data=payload
        )
        data = await response.text()
        if data:
            return lavalink_dictovert(json.loads(data))
        return {}
