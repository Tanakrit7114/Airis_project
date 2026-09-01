# Phase 3.7 — Hybrid Memory Retrieval

from app.memory.store import MemoryStore
from app.memory.vector_index import MemoryVectorIndex
from app.memory.ranking import MemoryRanker


class HybridMemoryRetriever:
    """
    Hybrid memory retrieval.

    Retrieval sources:

        1. Semantic Vector Search
        2. Exact Key Search
        3. Lexical / Store Search

    Flow:

        Query
          ↓
        Candidate Collection
          ↓
        Semantic Score
          +
        Exact Score
          ↓
        Hybrid Score
          ↓
        Ranking
    """

    def __init__(
        self,
        store=None,
        vector_index=None,
    ):
        self.store = (
            store
            if store is not None
            else MemoryStore()
        )

        self.vector_index = (
            vector_index
            if vector_index is not None
            else MemoryVectorIndex()
        )

        self.ranker = MemoryRanker()

    # ========================================================
    # Exact / lexical matching
    # ========================================================

    def _normalize_text(self, text):
        if not isinstance(text, str):
            return ""

        return (
            text.lower()
            .strip()
            .replace("_", " ")
            .replace("-", " ")
        )

    def _exact_match_score(
        self,
        query,
        memory,
    ):
        """
        Calculate exact / lexical relevance.

        Scores:

            1.00 = exact key
            0.90 = query contained in key
            0.80 = query contained in content
            0.70 = query contained in value
            otherwise word overlap
        """

        if not isinstance(query, str):
            return 0.0

        query = self._normalize_text(query)

        if not query:
            return 0.0

        key = self._normalize_text(
            memory.get("key", "")
        )

        value = self._normalize_text(
            memory.get("value", "")
        )

        content = self._normalize_text(
            memory.get("content", "")
        )

        # ----------------------------------------------------
        # Exact key
        # ----------------------------------------------------

        if query == key:
            return 1.0

        # ----------------------------------------------------
        # Query contained in key
        # ----------------------------------------------------

        if query in key:
            return 0.9

        # ----------------------------------------------------
        # Query contained in content
        # ----------------------------------------------------

        if query in content:
            return 0.8

        # ----------------------------------------------------
        # Query contained in value
        # ----------------------------------------------------

        if query in value:
            return 0.7

        # ----------------------------------------------------
        # Word overlap
        # ----------------------------------------------------

        query_words = set(
            query.split()
        )

        if not query_words:
            return 0.0

        searchable = (
            f"{key} {value} {content}"
        )

        searchable_words = set(
            searchable.split()
        )

        overlap = (
            query_words
            & searchable_words
        )

        if not overlap:
            return 0.0

        return (
            len(overlap)
            / len(query_words)
        )
        
    def _intent_key_score(self, query, memory):
            """
            Estimate how strongly the query matches
            the semantic meaning of a memory key.
            """

            if not isinstance(query, str):
                return 0.0

            query = self._normalize_text(query)

            key = self._normalize_text(
                memory.get("key", "")
            )

            if not query or not key:
                return 0.0

            # ------------------------------------------------
            # Query intent → memory key
            # ------------------------------------------------

            intent_map = {
                "favorite_programming_language": [
                    "programming language",
                    "language do i like",
                    "language do i prefer",
                    "favorite language",
                    "coding language",
                ],

                "current_project": [
                    "what am i building",
                    "what am i working on",
                    "current project",
                    "project am i working on",
                    "what project",
                    "building",
                ],

                "major": [
                    "what do i study",
                    "what am i majoring in",
                    "my major",
                    "what do i study at university",
                    "field of study",
                ],

                "favorite_drink": [
                    "what do i drink",
                    "drink do i like",
                    "favorite drink",
                    "what drink",
                ],

                "favorite_food": [
                    "what food do i like",
                    "favorite food",
                    "food do i like",
                    "what kind of food",
                ],

                "favorite_color": [
                    "what color do i like",
                    "favorite color",
                    "color do i like",
                ],

                "hardware": [
                    "what computer",
                    "what laptop",
                    "what machine",
                    "computer am i using",
                    "laptop do i have",
                    "machine do i work on",
                ],

                "preference": [
                    "what do i normally use",
                    "what do i usually use",
                    "what do i use for programming",
                    "what do i use for ai",
                ],
            }

            patterns = intent_map.get(key, [])

            for pattern in patterns:
                if pattern in query:
                    return 1.0

            # ------------------------------------------------
            # Word-level intent matching
            # ------------------------------------------------

            query_words = set(query.split())

            best_score = 0.0

            for pattern in patterns:
                pattern_words = set(
                    pattern.split()
                )

                if not pattern_words:
                    continue

                overlap = (
                    query_words & pattern_words
                )

                score = (
                    len(overlap)
                    / len(pattern_words)
                )

                best_score = max(
                    best_score,
                    score,
                )

            return best_score
        
    def _detect_query_intent(self, query):
        """
        Detect the type of memory the user is asking for.
        Returns the expected memory key or None.
        """

        if not isinstance(query, str):
            return None

        q = query.lower().strip()

        # Programming language
        if (
            "programming language" in q
            or "language do i prefer" in q
            or "language do i like" in q
        ):
            return "favorite_programming_language"

        # Programming usage
        if (
            "use for programming" in q
            or "normally use for programming" in q
        ):
            return "preference"
        
                # Programming usage
        # Must come before favorite programming language
        # because "preferred coding language" can refer to usage.
        if (
            "usually code in" in q
            or "normally code in" in q
            or "use for programming" in q
            or "normally use for programming" in q
            or "usually use for programming" in q
            or "use for coding" in q
            or "usually use for coding" in q
            or "normally use for coding" in q
        ):
            return "preference"

        # Favorite programming language
        if (
            "programming language" in q
            or "coding language do i like" in q
            or "language do i prefer" in q
            or "language do i like" in q
            or "coding language do i prefer" in q
            or "preferred coding language" in q
        ):
            return "favorite_programming_language"
        
        # Drink
        if (
            "what do i drink" in q
            or "drink do i like" in q
            or "favorite drink" in q
        ):
            return "favorite_drink"

        # Food
        if (
            "what kind of food" in q
            or "food do i like" in q
            or "favorite food" in q
        ):
            return "favorite_food"

        # Color
        if (
            "what color" in q
            or "color do i like" in q
            or "favorite color" in q
        ):
            return "favorite_color"

        # Hardware
        if (
            "what laptop" in q
            or "what computer" in q
            or "what machine" in q
            or "hardware" in q
        ):
            return "hardware"

        # Current project
        if (
            "what project" in q
            or "currently working on" in q
            or "what am i building" in q
            or "what i'm building" in q
        ):
            return "current_project"

        # Major / study
        if (
            "what do i study" in q
            or "what am i majoring in" in q
            or "my major" in q
        ):
            return "major"

        return None

    # ========================================================
    # Search
    # ========================================================

    def search(
        self,
        query,
        limit=5,
        min_similarity=0.0,
    ):
        """
        Search memories using hybrid retrieval.

        Score:

            70% semantic similarity
            30% exact / lexical score
        """

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        try:
            min_similarity = float(
                min_similarity
            )
        except (
            TypeError,
            ValueError,
        ):
            min_similarity = 0.0

        # ----------------------------------------------------
        # Semantic retrieval
        # ----------------------------------------------------

        try:
            semantic_results = (
                self.vector_index.search(
                    query,
                    limit=max(limit, 8),
                    min_similarity=min_similarity,
                )
            )
        except Exception:
            semantic_results = []

        # ----------------------------------------------------
        # Semantic score map
        # ----------------------------------------------------

        semantic_by_id = {}

        for result in semantic_results:
            memory_id = result.get(
                "memory_id"
            )

            if not memory_id:
                continue

            try:
                similarity = float(
                    result.get(
                        "similarity",
                        0.0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                similarity = 0.0

            semantic_by_id[
                str(memory_id)
            ] = similarity

        # ----------------------------------------------------
        # Candidate pool
        # ----------------------------------------------------

        candidates = {}

        # ====================================================
        # 1. Semantic candidates
        # ====================================================

        for result in semantic_results:
            memory_id = result.get(
                "memory_id"
            )

            if not memory_id:
                continue

            memory = self.store.get_memory(
                memory_id
            )

            if not memory:
                continue

            candidates[
                str(memory_id)
            ] = memory

        # ====================================================
        # 2. Exact key candidate
        # ====================================================

        try:
            exact_memory = (
                self.store.get_memory_by_key(
                    query
                )
            )
        except Exception:
            exact_memory = None

        if exact_memory:
            memory_id = exact_memory.get(
                "memory_id"
            )

            if memory_id:
                candidates[
                    str(memory_id)
                ] = exact_memory

        # ====================================================
        # 3. Store / lexical fallback
        # ====================================================

        try:
            store_memories = (
                self.store.active_memories()
            )
        except Exception:
            store_memories = []

        for memory in store_memories:
            if not isinstance(memory, dict):
                continue

            memory_id = memory.get(
                "memory_id"
            )

            if memory_id is None:
                continue

            candidates[
                str(memory_id)
            ] = memory

        # ----------------------------------------------------
        # Nothing found
        # ----------------------------------------------------

        if not candidates:
            return []

        # ----------------------------------------------------
        # Hybrid scoring
        # ----------------------------------------------------

        ranked = []

        for memory_id, memory in candidates.items():

            similarity = semantic_by_id.get(
                str(memory_id),
                0.0,
            )

            exact_score = (
                self._exact_match_score(
                    query,
                    memory,
                )
            )

            # ------------------------------------------------
            # Important:
            #
            # Store/lexical candidates don't have a vector.
            # Therefore similarity may be 0.
            #
            # They must still be allowed into the candidate
            # pool because lexical/exact retrieval is one of
            # the hybrid retrieval sources.
            # ------------------------------------------------

            if (
                similarity < min_similarity
                and exact_score <= 0.0
            ):
                continue

            memory_id = memory.get("memory_id")

            semantic_score = semantic_by_id.get(
                str(memory_id),
                0.0,
            )

            exact_score = self._exact_match_score(
                query,
                memory,
            )

            intent_key = self._detect_query_intent(query)

            intent_boost = 0.0

            if intent_key is not None:
                if str(memory.get("key")) == intent_key:
                    intent_boost = 0.20

            hybrid_score = (
                0.70 * similarity
                + 0.30 * exact_score
                + intent_boost
            )

            result = dict(memory)

            result["similarity"] = (
                similarity
            )

            result["exact_score"] = (
                exact_score
            )

            result["hybrid_score"] = (
                hybrid_score
            )

            ranked.append(result)

        # ----------------------------------------------------
        # Ranking
        # ----------------------------------------------------

        ranked.sort(
            key=lambda item: (
                item.get(
                    "hybrid_score",
                    0.0,
                ),
                item.get(
                    "exact_score",
                    0.0,
                ),
                item.get(
                    "similarity",
                    0.0,
                ),
                item.get(
                    "importance",
                    0.0,
                ),
                item.get(
                    "confidence",
                    0.0,
                ),
            ),
            reverse=True,
        )

        return ranked[:limit]

    # ========================================================
    # Re-ranking
    # ========================================================

    def rerank(
        self,
        query,
        limit=5,
        min_similarity=0.0,
    ):
        """
        Re-rank hybrid retrieval results.

        Final relevance:

            60% hybrid score
            40% MemoryRanker score
        """

        if not isinstance(query, str):
            return []

        query = query.strip()

        if not query:
            return []

        if limit <= 0:
            return []

        results = self.search(
            query,
            limit=max(limit, 8),
            min_similarity=min_similarity,
        )

        if not results:
            return []

        ranked = []

        for memory in results:

            hybrid_score = float(
                memory.get(
                    "hybrid_score",
                    0.0,
                )
            )

            importance = float(
                memory.get(
                    "importance",
                    0.0,
                )
            )

            confidence = float(
                memory.get(
                    "confidence",
                    0.0,
                )
            )

            ranking_score = self.ranker.score(
                query,
                memory,
            )

            normalized_ranking = (
                self._normalize_ranking(
                    ranking_score
                )
            )

            relevance_score = (
                0.60 * hybrid_score
                + 0.40 * normalized_ranking
            )

            result = dict(memory)

            result["importance"] = (
                importance
            )

            result["confidence"] = (
                confidence
            )

            result["ranking_score"] = (
                ranking_score
            )

            result["relevance_score"] = (
                relevance_score
            )

            ranked.append(result)

        # ----------------------------------------------------
        # Final ranking
        # ----------------------------------------------------

        ranked.sort(
            key=lambda item: (
                item.get(
                    "relevance_score",
                    0.0,
                ),
                item.get(
                    "hybrid_score",
                    0.0,
                ),
                item.get(
                    "exact_score",
                    0.0,
                ),
                item.get(
                    "similarity",
                    0.0,
                ),
                item.get(
                    "importance",
                    0.0,
                ),
                item.get(
                    "confidence",
                    0.0,
                ),
            ),
            reverse=True,
        )

        return ranked[:limit]

    # ========================================================
    # Best reranked
    # ========================================================

    def best_reranked(
        self,
        query,
        min_similarity=0.0,
    ):
        results = self.rerank(
            query,
            limit=1,
            min_similarity=min_similarity,
        )

        if not results:
            return None

        return results[0]

    # ========================================================
    # Best hybrid
    # ========================================================

    def best(
        self,
        query,
        min_similarity=0.0,
    ):
        results = self.search(
            query,
            limit=1,
            min_similarity=min_similarity,
        )

        if not results:
            return None

        return results[0]

    # ========================================================
    # Normalize ranking
    # ========================================================

    def _normalize_ranking(self, score):
        """
        Convert MemoryRanker score into approximately 0-1.

        The ranker may already return a normalized value.
        """

        try:
            score = float(score)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if score < 0.0:
            return 0.0

        if score > 1.0:
            return 1.0

        return score