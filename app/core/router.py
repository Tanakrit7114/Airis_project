import ast
import operator as op
import re
from app.tools.extensions_tools import detect_extension_intent


# ============================================================
# Calculator
# ============================================================

OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
}


def extract_calculation(text: str) -> str:
    text = text.strip()

    prefixes = [
        "calculate ",
        "compute ",
        "คำนวณ ",
    ]

    lower = text.lower()

    for prefix in prefixes:
        if lower.startswith(prefix):
            return text[len(prefix):].strip()

    return text


def is_calculation(text: str) -> bool:
    text = text.strip().lower()

    patterns = [
        r"^calculate\s+[\d\s+\-*/().]+$",
        r"^compute\s+[\d\s+\-*/().]+$",
        r"^คำนวณ\s+[\d\s+\-*/().]+$",
        r"^[\d\s+\-*/().]+$",
        r"^what\s+is\s+[\d\s+\-*/().]+[?]?$",
    ]

    return any(re.match(pattern, text) for pattern in patterns)


def calculate(expression: str):
    node = ast.parse(expression, mode="eval").body
    return _evaluate(node)


def _evaluate(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Invalid number")

    if isinstance(node, ast.BinOp):
        operator = OPERATORS.get(type(node.op))

        if operator is None:
            raise ValueError("Unsupported operator")

        return operator(
            _evaluate(node.left),
            _evaluate(node.right),
        )

    if isinstance(node, ast.UnaryOp):
        operator = OPERATORS.get(type(node.op))

        if operator is None:
            raise ValueError("Unsupported operator")

        return operator(_evaluate(node.operand))

    raise ValueError("Invalid expression")


# ============================================================
# Router
# ============================================================

class Router:

    def route(self, text: str) -> str:

        text = text.strip()
        t = text.lower()

        # ----------------------------------------------------
        # 1. Calculator
        # ----------------------------------------------------

        if is_calculation(text):
            return "tool:calculator"

        # ----------------------------------------------------
        # 2. System
        # ----------------------------------------------------

        system_patterns = [
            "today",
            "today is",
            "what date",
            "what's the date",
            "what is the date",
            "current date",
            "what time",
            "what's the time",
            "what is the time",
            "current time",

            "วันที่วันนี้",
            "วันนี้วันที่เท่าไหร่",
            "วันนี้วันอะไร",
            "ตอนนี้กี่โมง",
            "เวลาเท่าไหร่",
        ]

        if any(pattern in t for pattern in system_patterns):
            return "tool:system"

        # ----------------------------------------------------
        # 3. Connected extension intents
        # ----------------------------------------------------

        extension_intent = detect_extension_intent(text)
        if extension_intent:
            return "extension:" + extension_intent["tool"]

        # ----------------------------------------------------
        # 4. Search
        # ----------------------------------------------------

        search_words = [
            "latest",
            "news",
            "search",
            "research",
            "sources",
            "source",
            "citation",
            "cite",
            "current",
            "ราคา",
            "ล่าสุด",
            "ค้นหา",
            "หาข้อมูล",
            "อ้างอิง",
            "แหล่งข้อมูล",
            "แหล่งอ้างอิง",
            "ข่าว",
            "ปัจจุบัน",
        ]

        if any(word in t for word in search_words):
            return "search"

        # ----------------------------------------------------
        # 4. Default
        # ----------------------------------------------------

        return "memory_llm"
