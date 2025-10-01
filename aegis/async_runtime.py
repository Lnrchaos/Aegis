"""
Async runtime support for Aegis
Provides async/await primitives and event loop management.
"""

from __future__ import annotations
import asyncio
import time
from typing import Any, Callable, List, Dict, Optional
from dataclasses import dataclass
from .runtime import Environment, NativeFunction, RuntimeErrorAegis


@dataclass
class Promise:
    """Represents an async operation that may complete in the future."""
    value: Any = None
    error: Optional[Exception] = None
    resolved: bool = False
    callbacks: List[Callable] = None
    
    def __post_init__(self):
        if self.callbacks is None:
            self.callbacks = []
    
    def then(self, callback: Callable) -> 'Promise':
        """Chain a callback to be called when the promise resolves."""
        if self.resolved:
            if self.error:
                raise self.error
            callback(self.value)
        else:
            self.callbacks.append(callback)
        return self
    
    def resolve(self, value: Any) -> None:
        """Resolve the promise with a value."""
        self.value = value
        self.resolved = True
        for callback in self.callbacks:
            callback(value)
    
    def reject(self, error: Exception) -> None:
        """Reject the promise with an error."""
        self.error = error
        self.resolved = True
        for callback in self.callbacks:
            callback(error)


class AsyncRuntime:
    """Manages async operations and event loop."""
    
    def __init__(self):
        self.loop = None
        self.tasks: List[asyncio.Task] = []
        self.timers: Dict[str, Any] = {}
        
    def start_loop(self) -> None:
        """Start the event loop if not already running."""
        if self.loop is None or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
    
    def stop_loop(self) -> None:
        """Stop the event loop and clean up."""
        if self.loop and not self.loop.is_closed():
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
            self.loop.close()
    
    def create_promise(self) -> Promise:
        """Create a new promise."""
        return Promise()
    
    def sleep(self, seconds: float) -> Promise:
        """Create a promise that resolves after the given delay."""
        promise = self.create_promise()
        
        def resolve_after():
            time.sleep(seconds)
            promise.resolve(None)
        
        # Run in background thread to avoid blocking
        import threading
        thread = threading.Thread(target=resolve_after)
        thread.daemon = True
        thread.start()
        
        return promise
    
    def timeout(self, promise: Promise, seconds: float) -> Promise:
        """Create a promise that rejects if the given promise doesn't resolve in time."""
        timeout_promise = self.create_promise()
        
        def timeout_handler():
            time.sleep(seconds)
            if not promise.resolved:
                timeout_promise.reject(TimeoutError(f"Operation timed out after {seconds} seconds"))
        
        import threading
        thread = threading.Thread(target=timeout_handler)
        thread.daemon = True
        thread.start()
        
        return timeout_promise
    
    def all(self, promises: List[Promise]) -> Promise:
        """Create a promise that resolves when all given promises resolve."""
        all_promise = self.create_promise()
        results = []
        completed = 0
        
        def check_completion():
            nonlocal completed
            completed += 1
            if completed == len(promises):
                all_promise.resolve(results)
        
        for i, promise in enumerate(promises):
            def make_handler(index):
                def handler(value):
                    results[index] = value
                    check_completion()
                return handler
            
            promise.then(make_handler(i))
        
        return all_promise
    
    def race(self, promises: List[Promise]) -> Promise:
        """Create a promise that resolves with the first promise to resolve."""
        race_promise = self.create_promise()
        
        def resolve_first(value):
            if not race_promise.resolved:
                race_promise.resolve(value)
        
        for promise in promises:
            promise.then(resolve_first)
        
        return race_promise


# Global async runtime instance
_async_runtime = AsyncRuntime()


def get_async_runtime() -> AsyncRuntime:
    """Get the global async runtime instance."""
    return _async_runtime


def make_async_functions() -> Dict[str, Any]:
    """Create async-related native functions for the environment."""
    
    def async_sleep(args: List[Any]) -> Any:
        """Native function for async sleep."""
        if not args:
            return _async_runtime.sleep(0)
        seconds = float(args[0])
        return _async_runtime.sleep(seconds)
    
    def async_timeout(args: List[Any]) -> Any:
        """Native function for async timeout."""
        if len(args) < 2:
            raise RuntimeErrorAegis("timeout requires promise and seconds")
        promise = args[0]
        seconds = float(args[1])
        return _async_runtime.timeout(promise, seconds)
    
    def async_all(args: List[Any]) -> Any:
        """Native function for async all."""
        if not args:
            return _async_runtime.all([])
        return _async_runtime.all(args)
    
    def async_race(args: List[Any]) -> Any:
        """Native function for async race."""
        if not args:
            raise RuntimeErrorAegis("race requires at least one promise")
        return _async_runtime.race(args)
    
    def async_promise(args: List[Any]) -> Any:
        """Native function to create a new promise."""
        return _async_runtime.create_promise()
    
    return {
        "sleep": NativeFunction("sleep", async_sleep),
        "timeout": NativeFunction("timeout", async_timeout),
        "all": NativeFunction("all", async_all),
        "race": NativeFunction("race", async_race),
        "promise": NativeFunction("promise", async_promise),
    }
