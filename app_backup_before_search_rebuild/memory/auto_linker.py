# Phase 5.1 — Automatic Memory Linking

from app.memory.hybrid_retrieval import HybridMemoryRetriever
from app.memory.memory_graph import MemoryGraph


class MemoryAutoLinker:
    """
    Automatically discover and create relationships
    between related memories.
    """

    def __init__(
        self,
        store,
        graph=None,
        graph_store=None,
        retriever=None,
    ):
        self.store = store

        self.graph = (
            graph
            if graph is not None
            else MemoryGraph()
        )

        self.graph_store = graph_store

        self.retriever = (
            retriever
            if retriever is not None
            else HybridMemoryRetriever(
                store=store
            )
        )

    # ========================================================
    # Link Memory
    # ========================================================

    def link_memory(
        self,
        memory_id,
        limit=5,
        min_similarity=0.2,
        relation="related_to",
    ):
        """
        Find memories related to memory_id
        and create graph links.
        """

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if memory_id is None:
            return []

        if limit <= 0:
            return []

        memory = self.store.get_memory(
            memory_id
        )

        if not memory:
            return []

        # ----------------------------------------------------
        # Build search query
        # ----------------------------------------------------

        query_parts = [
            str(memory.get("key", "")),
            str(memory.get("value", "")),
            str(memory.get("content", "")),
        ]

        query = " ".join(
            part
            for part in query_parts
            if part
        ).strip()

        if not query:
            return []

        # ----------------------------------------------------
        # Retrieve related memories
        # ----------------------------------------------------

        try:
            results = self.retriever.search(
                query,
                limit=max(limit + 1, 8),
                min_similarity=min_similarity,
            )
        except Exception:
            return []

        if not results:
            return []

        linked = []

        # ----------------------------------------------------
        # Create links
        # ----------------------------------------------------

        for candidate in results:

            candidate_id = candidate.get(
                "memory_id"
            )

            if candidate_id is None:
                continue

            # Never link memory to itself
            if str(candidate_id) == str(memory_id):
                continue

            # ------------------------------------------------
            # Relationship strength
            # ------------------------------------------------

            try:
                strength = float(
                    candidate.get(
                        "hybrid_score",
                        candidate.get(
                            "similarity",
                            0.0,
                        ),
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                strength = 0.0

            # ------------------------------------------------
            # Avoid duplicate links
            # ------------------------------------------------

            duplicate = False

            for existing in self.graph.all_links():

                if (
                    str(existing.source_id)
                    == str(memory_id)
                    and
                    str(existing.target_id)
                    == str(candidate_id)
                    and
                    str(existing.relation)
                    == str(relation)
                ):
                    duplicate = True
                    break

            if duplicate:
                continue

            # ------------------------------------------------
            # Create graph link
            # ------------------------------------------------

            link = self.graph.add_link(
                source_id=memory_id,
                target_id=candidate_id,
                relation=relation,
                strength=strength,
            )

            if self.graph_store is not None:
                self.graph_store.add_link(
                    source_id=memory_id,
                    target_id=candidate_id,
                    relation=relation,
                    strength=strength,
                )

            linked.append(link)

            if len(linked) >= limit:
                break

        return linked
    
        # ========================================================
        # Relationship Scoring
        # ========================================================

    def relationship_score(
        self,
        first_memory_id,
        second_memory_id,
    ):
        """
        Calculate relationship strength between two memories.

        Signals:
            - Shared entities
            - Shared tags
            - Same memory type
            - Same subject
            - Semantic similarity
            - Importance
            - Confidence

        Returns:
            float between 0.0 and 1.0
        """

        if first_memory_id is None:
            return 0.0

        if second_memory_id is None:
            return 0.0

        if str(first_memory_id) == str(second_memory_id):
            return 1.0

        first = self.store.get_memory(
            first_memory_id
        )

        second = self.store.get_memory(
            second_memory_id
        )

        if not first or not second:
            return 0.0

        # ----------------------------------------------------
        # Shared entities
        # ----------------------------------------------------

        first_entities = set(
            str(item).strip().lower()
            for item in first.get("entities", [])
            if item
        )

        second_entities = set(
            str(item).strip().lower()
            for item in second.get("entities", [])
            if item
        )

        shared_entities = (
            first_entities & second_entities
        )

        entity_score = 0.0

        if first_entities or second_entities:
            union = (
                first_entities | second_entities
            )

            if union:
                entity_score = (
                    len(shared_entities)
                    / len(union)
                )

        # ----------------------------------------------------
        # Shared tags
        # ----------------------------------------------------

        first_tags = set(
            str(item).strip().lower()
            for item in first.get("tags", [])
            if item
        )

        second_tags = set(
            str(item).strip().lower()
            for item in second.get("tags", [])
            if item
        )

        shared_tags = (
            first_tags & second_tags
        )

        tag_score = 0.0

        if first_tags or second_tags:
            union = (
                first_tags | second_tags
            )

            if union:
                tag_score = (
                    len(shared_tags)
                    / len(union)
                )

        # ----------------------------------------------------
        # Same memory type
        # ----------------------------------------------------

        type_score = 0.0

        if (
            first.get("memory_type")
            and
            second.get("memory_type")
            and
            str(first.get("memory_type")).lower()
            ==
            str(second.get("memory_type")).lower()
        ):
            type_score = 1.0

        # ----------------------------------------------------
        # Same subject
        # ----------------------------------------------------

        subject_score = 0.0

        if (
            first.get("subject")
            and
            second.get("subject")
            and
            str(first.get("subject")).lower()
            ==
            str(second.get("subject")).lower()
        ):
            subject_score = 1.0

        # ----------------------------------------------------
        # Semantic similarity
        # ----------------------------------------------------

        semantic_score = 0.0

        try:
            first_text = str(
                first.get(
                    "content",
                    f"{first.get('key', '')}: "
                    f"{first.get('value', '')}",
                )
            )

            second_text = str(
                second.get(
                    "content",
                    f"{second.get('key', '')}: "
                    f"{second.get('value', '')}",
                )
            )

            if first_text.strip() and second_text.strip():
                results = self.retriever.search(
                    first_text,
                    limit=20,
                    min_similarity=0.0,
                )

                for result in results:
                    result_id = result.get(
                        "memory_id"
                    )

                    if (
                        str(result_id)
                        == str(second_memory_id)
                    ):
                        try:
                            similarity = result.get("similarity")

                            hybrid_score = result.get(
                                "hybrid_score",
                                0.0,
                            )

                            try:
                                similarity = float(similarity)
                            except (TypeError, ValueError):
                                similarity = 0.0

                            try:
                                hybrid_score = float(hybrid_score)
                            except (TypeError, ValueError):
                                hybrid_score = 0.0

                            semantic_score = max(
                                similarity,
                                hybrid_score,
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            semantic_score = 0.0

                        break

        except Exception:
            semantic_score = 0.0

        # ----------------------------------------------------
        # Memory quality
        # ----------------------------------------------------

        try:
            importance_first = float(
                first.get(
                    "importance",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            importance_first = 0.0

        try:
            importance_second = float(
                second.get(
                    "importance",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            importance_second = 0.0

        try:
            confidence_first = float(
                first.get(
                    "confidence",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence_first = 0.0

        try:
            confidence_second = float(
                second.get(
                    "confidence",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence_second = 0.0

        importance_score = (
            importance_first
            + importance_second
        ) / 2.0

        confidence_score = (
            confidence_first
            + confidence_second
        ) / 2.0

        # ----------------------------------------------------
        # Final relationship score
        # ----------------------------------------------------

        score = (
            0.45 * semantic_score
            + 0.25 * entity_score
            + 0.15 * tag_score
            + 0.05 * type_score
            + 0.05 * subject_score
            + 0.025 * importance_score
            + 0.025 * confidence_score
        )

        return max(
            0.0,
            min(1.0, float(score)),
        )
    
    # ========================================================
    # Intelligent Auto Linking
    # ========================================================

    def auto_link(
        self,
        memory_id,
        limit=5,
        min_relationship=0.4,
        relation="related_to",
    ):
        """
        Automatically create links for strongly related memories.

        Uses relationship_score() to determine whether
        a candidate should be linked.
        """

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if memory_id is None:
            return []

        if limit <= 0:
            return []

        memory = self.store.get_memory(memory_id)

        if not memory:
            return []

        # ----------------------------------------------------
        # Collect candidate memories
        # ----------------------------------------------------

        try:
            candidates = self.store.active_memories()
        except Exception:
            return []

        if not candidates:
            return []

        scored = []

        # ----------------------------------------------------
        # Score relationships
        # ----------------------------------------------------

        for candidate in candidates:

            candidate_id = candidate.get("memory_id")

            if candidate_id is None:
                continue

            # Never link memory to itself
            if str(candidate_id) == str(memory_id):
                continue

            try:
                score = float(
                    self.relationship_score(
                        memory_id,
                        candidate_id,
                    )
                )
            except Exception:
                continue

            # Reject weak relationships
            if score < min_relationship:
                continue

            scored.append(
                (
                    score,
                    candidate_id,
                )
            )

        if not scored:
            return []

        # ----------------------------------------------------
        # Strongest relationships first
        # ----------------------------------------------------

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        linked = []

        # ----------------------------------------------------
        # Create links
        # ----------------------------------------------------

        for score, candidate_id in scored:

            # Check duplicate
            duplicate = False

            for existing in self.graph.all_links():

                if (
                    str(existing.source_id)
                    == str(memory_id)
                    and
                    str(existing.target_id)
                    == str(candidate_id)
                    and
                    str(existing.relation)
                    == str(relation)
                ):
                    duplicate = True
                    break

            if duplicate:
                continue

            link = self.graph.add_link(
                source_id=memory_id,
                target_id=candidate_id,
                relation=relation,
                strength=score,
            )

            if self.graph_store is not None:
                self.graph_store.add_link(
                    source_id=memory_id,
                    target_id=candidate_id,
                    relation=relation,
                    strength=score,
                )

            linked.append(link)

            if len(linked) >= limit:
                break

        return linked

