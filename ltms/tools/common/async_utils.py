"""
LTMC Async Utilities
Proper async handling for MCP server context following python-mcp-sdk patterns
"""

import asyncio
import threading
import concurrent.futures
from typing import Any, Coroutine, TypeVar
import functools

T = TypeVar('T')


def run_async_in_context(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine in the correct context.
    
    This function handles the event loop conflicts that occur when trying to run
    async code from within an already running event loop (like in MCP servers).
    
    Following python-mcp-sdk best practices, this detects the current context
    and chooses the appropriate execution strategy.
    
    Args:
        coro: The coroutine to execute
        
    Returns:
        The result of the coroutine execution
        
    Raises:
        Exception: Any exception raised by the coroutine
    """
    try:
        # Check if we're already in an event loop
        current_loop = asyncio.get_running_loop()
        
        # We're in an event loop context (like MCP server)
        # Need to run in a separate thread with its own event loop
        return _run_in_new_thread(coro)
        
    except RuntimeError:
        # No running event loop - safe to use asyncio.run()
        return asyncio.run(coro)


def _run_in_new_thread(coro: Coroutine[Any, Any, T]) -> T:
    """Run coroutine in a new thread with its own event loop.
    
    This is the proper way to handle async operations when already
    within an event loop context, as recommended by python-mcp-sdk patterns.
    """
    def thread_target():
        # Create new event loop in thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(thread_target)
        return future.result(timeout=30)  # 30 second timeout


def async_to_sync(async_func):
    """Decorator to convert async function to sync using proper context handling.
    
    This decorator allows async functions to be called from sync contexts
    without causing event loop conflicts.
    
    Usage:
        @async_to_sync
        async def my_async_function():
            await some_async_operation()
            return result
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        coro = async_func(*args, **kwargs)
        return run_async_in_context(coro)
    
    return wrapper


async def safe_async_call(func, *args, **kwargs) -> Any:
    """Safely call a function that might be sync or async.
    
    This utility handles the case where you don't know if a function
    is sync or async, and ensures proper execution in either case.
    
    Args:
        func: Function to call (sync or async)
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Result of function call
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        # Re-raise with context
        raise e


def create_async_task_safe(coro: Coroutine[Any, Any, T]) -> T:
    """Create async task safely within event loop context.
    
    This is an alternative to run_async_in_context for cases where
    you want to schedule a task within the current event loop.
    
    Args:
        coro: Coroutine to schedule
        
    Returns:
        Task result
    """
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro)
        # This approach schedules the task but doesn't wait for it
        # Use only when you want fire-and-forget behavior
        return task
    except RuntimeError:
        # No running loop
        return asyncio.run(coro)