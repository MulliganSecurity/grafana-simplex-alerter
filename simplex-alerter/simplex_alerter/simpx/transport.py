import asyncio
import json
import websockets
from typing import Generic, TypeVar, Dict, Union, Optional, Any, AsyncIterator
from abc import ABC, abstractmethod

from .queuex import ABQueue, ABQueueError
from .response import ChatResponse

W = TypeVar('W')
R = TypeVar('R')

class TransportError(Exception):
    pass

class Transport(Generic[W, R], ABC):
    """Abstract base class for transport mechanisms."""
    
    def __init__(self, q_size: int):
        self.queue = ABQueue[R](q_size)
    
    def __aiter__(self) -> 'Transport[W, R]':
        return self
    
    async def __anext__(self) -> R:
        try:
            return await self.read()
        except ABQueueError:
            raise StopAsyncIteration
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def write(self, data: W) -> None:
        pass
    
    async def read(self) -> R:
        return await self.queue.dequeue()
    
    async def next(self):
        return await self.queue.next()

class ChatServer:
    """Configuration for a chat server."""
    
    def __init__(self, host: str, port: Optional[str] = None):
        self.host = host
        self.port = port

local_server = ChatServer(host="localhost", port="5225")

class ChatSrvRequest:
    """Request to the chat server."""
    
    def __init__(self, corr_id: str, cmd: str):
        self.corr_id = corr_id
        self.cmd = cmd

class ChatResponseError(Exception):
    """Error in chat response."""
    
    def __init__(self, message: str, data: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.data = data

class ChatSrvResponse:
    """Response from the chat server."""
    
    def __init__(self, corr_id: Optional[str], resp: ChatResponse):
        self.corr_id = corr_id
        self.resp = resp

class WSTransport(Transport[Union[bytes, str], Union[bytes, str]]):
    """WebSocket transport."""
    
    def __init__(self, socket, timeout: float, q_size: int):
        super().__init__(q_size)
        self.socket = socket
        self.timeout = timeout
    
    @classmethod
    async def connect(cls, url: str, timeout: float, q_size: int) -> 'WSTransport':
        """Connect to a WebSocket server."""
        try:
            socket = await asyncio.wait_for(websockets.connect(url), timeout)
            transport = cls(socket, timeout, q_size)
            
            # Start task to read messages from socket
            asyncio.create_task(transport._receive_loop())
            
            return transport
        except asyncio.TimeoutError:
            raise TimeoutError(f"Connection to {url} timed out after {timeout}s")
    async def _receive_loop(self):
        """Background task to receive messages from WebSocket."""
        try:
            async for message in self.socket:
                await self.queue.enqueue(message)
        except Exception as e:
            # On error, close the queue if not already closed
            if not self.queue.enq_closed:
                await self.queue.close()
        finally:
            # Only close the queue if not already closed
            if not self.queue.enq_closed:
                await self.queue.close()
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        await self.socket.close()
    
    async def write(self, data: Union[bytes, str]) -> None:
        """Send data to the WebSocket."""
        try:
            await asyncio.wait_for(self.socket.send(data), self.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Write operation timed out after {self.timeout}s")
    
    async def read_binary(self, size: int) -> bytes:
        """Read binary data from the WebSocket."""
        data = await self.read()
        if isinstance(data, str):
            raise TransportError("Invalid text block: expected binary")
        if len(data) != size:
            raise TransportError("Invalid block size")
        return data

class ChatTransport(Transport[ChatSrvRequest, Union[ChatSrvResponse, ChatResponseError]]):
    """Transport for chat server communication."""
    
    def __init__(self, ws: WSTransport, timeout: float, q_size: int):
        super().__init__(q_size)
        self.ws = ws
        self.timeout = timeout
    
    @classmethod
    async def connect(cls, srv: Union[ChatServer, str], timeout: float, q_size: int) -> 'ChatTransport':
        """Connect to a chat server."""
        if isinstance(srv, str):
            uri = srv
        else:
            port = srv.port or "5225"
            uri = f"ws://{srv.host}:{port}"
        
        ws = await WSTransport.connect(uri, timeout, q_size)
        transport = cls(ws, timeout, q_size)
        
        # Start task to process WebSocket messages
        asyncio.create_task(transport._process_ws_queue(ws))
        
        return transport
    
    async def _process_ws_queue(self, ws: WSTransport):
        """Process messages from the WebSocket."""
        async for data in ws:
            if not isinstance(data, str):
                await self.queue.enqueue(ChatResponseError("WebSocket data is not a string"))
                continue
            
            try:
                json_data = json.loads(data)
                if json_data.get('resp', {}).get('Right').get('type') and isinstance(json_data['resp']['Right']['type'], str):
                    # Parse the response as a ChatResponse object
                    resp = ChatSrvResponse(json_data.get('corrId'), json_data['resp']['Right'])
                else:
                    resp = ChatResponseError("Invalid response format", data)
                
                await self.queue.enqueue(resp)
            except Exception as e:
                await self.queue.enqueue(ChatResponseError(str(e), data))
        
        await self.queue.close()
    
    async def close(self) -> None:
        """Close the transport."""
        await self.ws.close()
    
    async def write(self, cmd: ChatSrvRequest) -> None:
        """Send a request to the chat server."""
        data = json.dumps({
            'corrId': cmd.corr_id,
            'cmd': cmd.cmd
        })
        await self.ws.write(data)

def noop() -> None:
    """Function that does nothing."""
    pass
