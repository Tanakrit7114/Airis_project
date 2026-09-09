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
from app.memory.memory_graph import MemoryGraph
from app.memory.graph_store import MemoryGraphStore
from app.memory.auto_linker import MemoryAutoLinker
from app.memory.hybrid_retrieval import HybridMemoryRetriever


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
            graph=None,
            auto_linker=None,
        ):

            self.extractor = extractor or MemoryExtractor()
            self.validator = validator or MemoryValidator()

            self.deduplicator = (
                deduplicator
                or MemoryDeduplicator()
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

            # ====================================================
            # Memory Graph
            # ====================================================

            self.graph = (
                graph
                if graph is not None
                else MemoryGraph()
            )

            # ====================================================
            # Persistent Memory Graph
            # ====================================================

            self.graph_store = MemoryGraphStore()

            self.graph_store.load_into_graph(
                self.graph
            )

            # ====================================================
            # Automatic Memory Linking
            # ====================================================

            self.auto_linker = (
                auto_linker
                or MemoryAutoLinker(
                    store=self.store,
                    graph=self.graph,
                    graph_store=self.graph_store,
                    retriever=HybridMemoryRetriever(
                        store=self.store,
                        vector_index=self.vector_index,
                    ),
                )
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

        # ----------------------------------------------------
        # Retrieve active memories
        # ----------------------------------------------------

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

        # ==========================================
        # 7. Store + Index + Auto Link
        # ==========================================
        return self.store_memories(memories)

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

            # --------------------------------------------
            # Retrieve stored memory
            # --------------------------------------------

            new_memory = self.store.get_memory_by_key(
                memory["key"]
            )

            if not new_memory:
                memory["contradictions"] = contradictions
                stored.append(memory)
                continue

            # --------------------------------------------
            # Attach contradiction information
            # --------------------------------------------

            new_memory["contradictions"] = contradictions

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

            # --------------------------------------------
            # Auto-link related memories
            # --------------------------------------------

            new_memory_id = new_memory.get(
                "memory_id"
            )

            if new_memory_id:

                self.auto_linker.auto_link(
                    memory_id=new_memory_id,
                    limit=5,
                    min_relationship=0.30,
                )

            # --------------------------------------------
            # Add to result ONCE
            # --------------------------------------------

            stored.append(new_memory)

        return stored
    
    def build_memory_graph(self):
        """
        Build a graph from active memories.
        """

        memories = self.store.active_memories()

        # Clear current graph
        self.graph = MemoryGraph()

        # ----------------------------------------------------
        # Add memory nodes
        # ----------------------------------------------------

        for memory in memories:
            key = memory.get("key")

            if not key:
                continue

            self.graph.add_node(
                key,
                memory.get("value"),
                "memory",
            )

        # ----------------------------------------------------
        # Known semantic relationships
        # ----------------------------------------------------

        relationships = {
            "current_project": [
                ("favorite_programming_language", "uses"),
                ("preference", "related_to"),
                ("hardware", "runs_on"),
            ],

            "preference": [
                ("favorite_programming_language", "related_to"),
            ],
        }

        # ----------------------------------------------------
        # Add edges
        # ----------------------------------------------------

        for source, targets in relationships.items():

            if source not in self.graph.nodes:
                continue

            for target, relation in targets:

                if target not in self.graph.nodes:
                    continue

                self.graph.add_edge(
                    source,
                    target,
                    relation,
                )

        return self.graph
    