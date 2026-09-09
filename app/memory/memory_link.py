# Phase 4.1 — Memory Linking


class MemoryLink:
    """
    Represent a relationship between two memories.

    A link describes how one memory is related to another.
    """

    def __init__(
        self,
        source_id,
        target_id,
        relation="related_to",
        strength=1.0,
    ):
        self.source_id = str(source_id)
        self.target_id = str(target_id)
        self.relation = str(relation)
        self.strength = max(
            0.0,
            min(1.0, float(strength)),
        )

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "strength": self.strength,
        }

    def __repr__(self):
        return (
            f"MemoryLink("
            f"{self.source_id} "
            f"-[{self.relation}]-> "
            f"{self.target_id}, "
            f"strength={self.strength}"
            f")"
        )