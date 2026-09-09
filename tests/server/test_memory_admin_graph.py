from app.server.memory_admin import MemoryAdmin
from app.memory.memory_link import MemoryLink


class FakeStore:
    def all_memories_v2(self):
        return [
            {
                "memory_id": "a",
                "value": "Python",
                "key": "language",
                "memory_type": "preference",
            },
            {
                "memory_id": "b",
                "value": "KKU",
                "key": "university",
                "memory_type": "profile",
            },
        ]


class FakeGraphStore:
    def all_links(self):
        return [MemoryLink("a", "b", "studies_at", 0.9)]


def test_memory_admin_graph_serializes_memory_links():
    admin = MemoryAdmin.__new__(MemoryAdmin)
    admin.store = FakeStore()
    admin.graph_store = FakeGraphStore()

    payload = admin.graph()

    assert {node["id"] for node in payload["nodes"]} == {"a", "b"}
    assert payload["edges"] == [
        {
            "source": "a",
            "target": "b",
            "relation": "studies_at",
            "strength": 0.9,
        }
    ]
