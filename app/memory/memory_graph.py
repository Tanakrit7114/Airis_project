# Phase 4.2 — Memory Graph

from app.memory.memory_link import MemoryLink


class MemoryGraph:
    """
    Store relationships between memories.
    """

    def __init__(self):
        self._links = []

    def add_link(
        self,
        source_id,
        target_id,
        relation="related_to",
        strength=1.0,
    ):
        link = MemoryLink(
            source_id,
            target_id,
            relation,
            strength,
        )

        self._links.append(link)

        return link

    def remove_link(
        self,
        source_id,
        target_id,
        relation=None,
    ):
        source_id = str(source_id)
        target_id = str(target_id)

        for index, link in enumerate(self._links):
            if (
                link.source_id == source_id
                and link.target_id == target_id
                and (
                    relation is None
                    or link.relation == str(relation)
                )
            ):
                del self._links[index]
                return True

        return False

    def get_links_from(self, memory_id):
        memory_id = str(memory_id)

        return [
            link
            for link in self._links
            if link.source_id == memory_id
        ]

    def get_links_to(self, memory_id):
        memory_id = str(memory_id)

        return [
            link
            for link in self._links
            if link.target_id == memory_id
        ]

    def get_connected_ids(self, memory_id):
        memory_id = str(memory_id)

        connected = []

        for link in self._links:
            if link.source_id == memory_id:
                connected.append(link.target_id)

            elif link.target_id == memory_id:
                connected.append(link.source_id)

        return list(dict.fromkeys(connected))

    def all_links(self):
        return list(self._links)

    def __len__(self):
        return len(self._links)

    def clear(self):
        self._links.clear()
