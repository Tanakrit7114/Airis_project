# Phase 2.5 — Memory Supersession
# app/memory/pipeline.py

from app.memory.vector_index import MemoryVectorIndex
from app.memory.extractor import MemoryExtractor
from app.memory.validator import MemoryValidator
from app.memory.deduplicator import MemoryDeduplicator
from app.memory.contradiction import ContradictionDetector
from app.memory.importance import ImportanceScorer
from app.memory.confidence import ConfidenceScorer
from app.memory.store import MemoryStore

from app.memory.vector_index import MemoryVectorIndex


class MemoryPipeline:
    """
    Central pipeline for processing extracted memories.

    Pipeline:

        Extract
        → Validate
        → Deduplicate
        → Contradiction
        → Score
        → Store / Supersede
    """

    def __init__(
        self,
        extractor=None,
        validator=None,
        deduplicator=None,
        contradiction_detector=None,
        importance_scorer=None,
        confidence_scorer=None,
        store=None,
        vector_index=None,
    ):

        self.extractor = extractor or MemoryExtractor()
        self.validator = validator or MemoryValidator()
        self.deduplicator = (
            deduplicator or MemoryDeduplicator()
        )
        self.contradiction_detector = (
            contradiction_detector
            or ContradictionDetector()
        )
        self.importance_scorer = (
            importance_scorer
            or ImportanceScorer()
        )
        self.confidence_scorer = (
            confidence_scorer
            or ConfidenceScorer()
        )
        self.store = store or MemoryStore()
        
        self.vector_index = (
            vector_index
            or MemoryVectorIndex()
        )

    def extract(self, text):
        return self.extractor.extract(text)

    def validate(self, memory):
        return self.validator.validate(memory)

    def deduplicate(self, memories):
        return self.deduplicator.deduplicate(memories)

    def find_contradictions(
        self,
        memory,
        existing_memories,
    ):
        return self.contradiction_detector.find_contradictions(
            memory,
            existing_memories,
        )

    def score_importance(self, memory):
        score = self.importance_scorer.score(memory)
        memory["importance"] = score
        return memory

    def score_confidence(self, memory):
        score = self.confidence_scorer.score(memory)
        memory["confidence"] = score
        return memory

    # ========================================================
    # Process
    # ========================================================

    def process(
        self,
        text,
        existing_memories=None,
    ):
        """
        Process a user message through the complete
        memory pipeline.
        """

        if not isinstance(text, str):
            return []

        text = text.strip()

        if not text:
            return []

        # If caller does not provide memories,
        # retrieve active memories from the store.
        if existing_memories is None:
            existing_memories = (
                self.store.active_memories()
            )

        # ==========================================
        # 1. Extract
        # ==========================================

        memories = self.extract(text)

        if not memories:
            return []

        # ==========================================
        # 2. Validate
        # ==========================================

        validated = []

        for memory in memories:

            result = self.validate(memory)

            if result:
                validated.append(memory)

        memories = validated

        if not memories:
            return []

        # ==========================================
        # 3. Deduplicate
        # ==========================================

        memories = self.deduplicate(memories)

        # ==========================================
        # 4. Contradiction detection
        # ==========================================

        for memory in memories:

            contradictions = (
                self.find_contradictions(
                    memory,
                    existing_memories,
                )
            )

            memory["contradictions"] = contradictions

        # ==========================================
        # 5. Importance scoring
        # ==========================================

        for memory in memories:
            self.score_importance(memory)

        # ==========================================
        # 6. Confidence scoring
        # ==========================================

        for memory in memories:
            self.score_confidence(memory)

        return memories

    # ========================================================
    # Store
    # ========================================================

    def store_memories(self, memories):
        """
        Persist processed memories.

        If a new memory contradicts an existing memory:

            old memory → superseded
            new memory → active
        """

        if not memories:
            return []

        stored = []

        for memory in memories:

            contradictions = memory.get(
                "contradictions",
                [],
            )

            # --------------------------------------------
            # Store new memory
            # --------------------------------------------

            self.store.add_memory(
                memory_type=memory["memory_type"],
                subject=memory["subject"],
                key=memory["key"],
                value=memory["value"],
                importance=memory.get(
                    "importance",
                    0.5,
                ),
                confidence=memory.get(
                    "confidence",
                    0.8,
                ),
                source=memory.get(
                    "source",
                    "conversation",
                ),
                tags=memory.get(
                    "tags",
                    [],
                ),
                entities=memory.get(
                    "entities",
                    [],
                ),
                relationships=memory.get(
                    "relationships",
                    [],
                ),
                decay_rate=memory.get(
                    "decay_rate",
                    0.0,
                ),
                expires_at=memory.get(
                    "expires_at",
                ),
            )
            
            new_memory = self.store.get_memory_by_key(
                memory["key"]
            )
            
            # --------------------------------------------
            # Index memory for semantic retrieval
            # --------------------------------------------
            self.vector_index.index_memory(
                new_memory
            )

            # --------------------------------------------
            # Retrieve the newly stored memory
            # --------------------------------------------

            new_memory = self.store.get_memory_by_key(
                memory["key"]
            )

            if not new_memory:
                stored.append(memory)
                continue

            # --------------------------------------------
            # Supersede contradictions
            # --------------------------------------------

            for old_memory in contradictions:

                old_memory_id = old_memory.get(
                    "memory_id"
                )

                new_memory_id = new_memory.get(
                    "memory_id"
                )

                if (
                    old_memory_id
                    and new_memory_id
                    and old_memory_id != new_memory_id
                ):

                    self.store.supersede_memory(
                        old_memory_id,
                        new_memory_id,
                    )

            # --------------------------------------------
            # Index memory for semantic search
            # --------------------------------------------

            self.vector_index.index_memory(
                new_memory
            )

            stored.append(new_memory)

        return stored