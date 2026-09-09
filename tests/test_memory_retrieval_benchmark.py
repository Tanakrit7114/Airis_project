import time

from app.memory.store import MemoryStore
from app.memory.orchestrator import MemoryOrchestrator


def build_store():
    store = MemoryStore()

    memories = [
        {
            "memory_type": "preference",
            "subject": "user",
            "key": "favorite_programming_language",
            "value": "Python",
            "importance": 0.9,
            "confidence": 0.95,
        },
        {
            "memory_type": "preference",
            "subject": "user",
            "key": "favorite_food",
            "value": "Italian food",
            "importance": 0.7,
            "confidence": 0.9,
        },
        {
            "memory_type": "preference",
            "subject": "user",
            "key": "favorite_drink",
            "value": "milk",
            "importance": 0.6,
            "confidence": 0.9,
        },
        {
            "memory_type": "project",
            "subject": "user",
            "key": "current_project",
            "value": "JARVIS",
            "importance": 1.0,
            "confidence": 0.95,
        },
        {
            "memory_type": "hardware",
            "subject": "user",
            "key": "hardware",
            "value": "MacBook Pro M5 Pro",
            "importance": 0.8,
            "confidence": 0.9,
        },
    ]

    for memory in memories:
        store.add_memory(**memory)

    return store


def test_retrieval_benchmark():
    store = build_store()

    orchestrator = MemoryOrchestrator(store)

    queries = [
        "What is my favorite programming language?",
        "What food do I like?",
        "What project am I building?",
        "What computer am I using?",
    ]

    timings = []

    for query in queries:
        start = time.perf_counter()

        results = orchestrator.retrieve(
            query,
            limit=5,
        )

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        print(f"\nQuery: {query}")
        print(f"Time: {elapsed:.4f}s")
        print(f"Results: {len(results)}")

        assert results is not None

    total = sum(timings)
    average = total / len(timings)

    print("\n" + "=" * 50)
    print("MEMORY RETRIEVAL BENCHMARK")
    print("=" * 50)
    print(f"Queries: {len(queries)}")
    print(f"Total time: {total:.4f}s")
    print(f"Average: {average:.4f}s")
    print(f"Queries/sec: {len(queries) / total:.2f}")
    print("=" * 50)
