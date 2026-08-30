class Router:
    def route(self, text: str) -> str:
        t = text.lower()

        search_words = [
            "latest", "today", "current", "news", "ราคา",
            "ล่าสุด", "วันนี้", "ตอนนี้", "ค้นหา", "หาข้อมูล"
        ]

        if any(word in t for word in search_words):
            return "search"

        return "memory_llm"
