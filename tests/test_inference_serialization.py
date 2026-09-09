import asyncio
import threading

import pytest

from app.server.inference import run_serialized


@pytest.mark.parametrize("cancel", [False, True])
def test_running_worker_keeps_lock_after_waiter_leaves(cancel):
    async def scenario():
        lock = asyncio.Lock()
        started, release = threading.Event(), threading.Event()
        second = threading.Event()
        def work():
            started.set()
            release.wait(3)
        waiter = asyncio.create_task(run_serialized(lock, work, timeout=None if cancel else .05))
        await asyncio.to_thread(started.wait, 1)
        try:
            if cancel:
                waiter.cancel()
            with pytest.raises(asyncio.CancelledError if cancel else asyncio.TimeoutError):
                await waiter
            assert lock.locked()
            following = asyncio.create_task(run_serialized(lock, second.set))
            await asyncio.sleep(.02)
            assert not second.is_set()
            release.set()
            await asyncio.wait_for(following, 1)
            assert second.is_set()
            assert not lock.locked()
        finally:
            release.set()
    asyncio.run(scenario())


def test_timed_out_queued_job_never_starts():
    async def scenario():
        lock = asyncio.Lock()
        executed = threading.Event()
        await lock.acquire()
        with pytest.raises(asyncio.TimeoutError):
            await run_serialized(lock, executed.set, timeout=.01)
        lock.release()
        await asyncio.sleep(.02)
        assert not executed.is_set()
    asyncio.run(scenario())


def test_failed_worker_releases_lock():
    async def scenario():
        lock=asyncio.Lock()
        def fail(): raise ValueError("test")
        with pytest.raises(ValueError):
            await run_serialized(lock, fail)
        assert not lock.locked()
    asyncio.run(scenario())
