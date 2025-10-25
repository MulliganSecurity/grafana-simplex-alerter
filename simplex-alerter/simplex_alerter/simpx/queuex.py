import asyncio
from typing import Generic, TypeVar, Optional, AsyncIterator, Union, Any

T = TypeVar('T')
QUEUE_CLOSED = object()

class ABQueueError(Exception):
    pass

class ABQueue(Generic[T]):
    """An async bounded queue implementation similar to the TypeScript version."""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.queue = []
        self.enq_event = asyncio.Event()
        self.deq_event = asyncio.Event()
        self.deq_event.set()  # Initially can enqueue
        self.enq_closed = False
        self.deq_closed = False
    
    def __aiter__(self) -> 'ABQueue[T]':
        return self
    
    async def __anext__(self) -> T:
        try:
            return await self.dequeue()
        except ABQueueError:
            raise StopAsyncIteration
    
    async def enqueue(self, item: T) -> None:
        """Add an item to the queue."""
        await self._enqueue(item)
    
    async def _enqueue(self, item: Union[T, Any]) -> None:
        """Internal method to add any item to the queue."""
        if self.enq_closed:
            raise ABQueueError("enqueue: queue closed")
        
        # Wait until there's room in the queue
        await self.deq_event.wait()
        
        self.queue.append(item)
        
        # If queue is full, block further enqueues
        if len(self.queue) >= self.max_size:
            self.deq_event.clear()
        
        # Signal that queue has an item
        self.enq_event.set()
    
    async def dequeue(self) -> T:
        """Remove and return an item from the queue."""
        if self.deq_closed:
            raise ABQueueError("dequeue: queue closed")
        
        # Wait until there's an item in the queue
        await self.enq_event.wait()
        
        item = self.queue.pop(0)
        
        # If this was the last item, block further dequeues until new items arrive
        if not self.queue:
            self.enq_event.clear()
        
        # Signal that there's room in the queue
        self.deq_event.set()
        
        if item is QUEUE_CLOSED:
            self.deq_closed = True
            raise ABQueueError("dequeue: queue closed")
        
        return item
    
    async def close(self) -> None:
        """Close the queue for future enqueues."""
        await self._enqueue(QUEUE_CLOSED)
        self.enq_closed = True
    
    async def next(self):
        """Return the next item for async iteration."""
        if self.deq_closed:
            return {"done": True}
        
        try:
            value = await self.dequeue()
            return {"value": value, "done": False}
        except ABQueueError:
            return {"done": True}
        except Exception as e:
            raise e
