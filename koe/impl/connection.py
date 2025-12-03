class Connection:
    def __init__(
        self, 
        protocol: str="http", 
        url: str="localhost", 
        port: int=80, 
        password: str=""
    ):
        self.protocol =  protocol
        self.url = url
        self.port = port
        self.password = password
    
    @property
    def route(self) -> str:
        return f"{self.protocol}://{self.url}:{self.port}"