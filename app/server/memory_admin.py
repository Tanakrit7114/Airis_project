import sqlite3
from typing import Any
from app.config import MEMORY_DB
from app.memory.store import MemoryStore
from app.memory.graph_store import MemoryGraphStore


class MemoryAdmin:
    def __init__(self):
        self.db_path = MEMORY_DB
        self.store = MemoryStore()
        self.graph_store = MemoryGraphStore()

    def list(self, query: str | None = None, status: str | None = None, limit: int = 100):
        if query:
            rows = self.store.search_memories(query, limit=limit)
        else:
            rows = self.store.all_memories_v2()
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows[:limit]

    def update(self, memory_id: str, **fields: Any):
        allowed = {"value", "importance", "confidence", "source", "tags", "entities", "relationships", "decay_rate", "expires_at"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.store.get_memory(memory_id)
        sets = []
        params = []
        for key, value in updates.items():
            if key in {"tags", "entities", "relationships"}:
                import json
                value = json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)
            sets.append(f"{key} = ?")
            params.append(value)
        if "value" in updates:
            existing = self.store.get_memory(memory_id) or {}
            key = existing.get("key", "value")
            sets.append("content = ?")
            params.append(f"{key}: {updates['value']}")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(memory_id)
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute(f"UPDATE memories SET {', '.join(sets)} WHERE memory_id = ?", params)
            con.commit()
            if cur.rowcount == 0:
                return None
        return self.store.get_memory(memory_id)

    def soft_delete(self, memory_id: str):
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute(
                "UPDATE memories SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE memory_id = ?",
                (memory_id,),
            )
            con.commit()
            return cur.rowcount > 0

    def graph(self):
        links = self.graph_store.all_links()
        memories = {str(m.get("memory_id")): m for m in self.store.all_memories_v2() if m.get("memory_id")}
        nodes = []
        ids = set()
        for link in links:
            ids.add(str(link.source_id))
            ids.add(str(link.target_id))
        for mid in ids:
            m = memories.get(mid, {})
            nodes.append({
                "id": mid,
                "label": m.get("value") or m.get("key") or mid,
                "type": m.get("memory_type", "memory"),
            })
        edges = []
        for link in links:
            edges.append({
                "source": str(link.source_id),
                "target": str(link.target_id),
                "relation": link.relation,
                "strength": link.strength,
            })
        return {"nodes": nodes, "edges": edges}
