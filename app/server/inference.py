"""Serialize native workers, even when their HTTP/WebSocket waiter goes away."""
import asyncio
from functools import partial

_workers: set[asyncio.Task] = set()


async def run_serialized(lock, function, *args, timeout=None, **kwargs):
    started = False

    async def work():
        nonlocal started
        async with lock:
            started = True
            return await asyncio.to_thread(partial(function, *args, **kwargs))

    task = asyncio.create_task(work())
    _workers.add(task)

    def finished(done):
        _workers.discard(done)
        if not done.cancelled():
            done.exception()  # Retrieve failures after the waiter has timed out.

    task.add_done_callback(finished)
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        # A queued request must never execute after its caller has left. Once
        # native work starts, only its owner may release the lock on completion.
        if not started:
            task.cancel()
        raise
