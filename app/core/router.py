import ast
import operator as op
import re


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
    """
    Extract mathematical expression from a user message.

    Examples:
        Calculate 123 + 456
        -> 123 + 456

        compute 10 * 20
        -> 10 * 20

        คำนวณ 100 / 5
        -> 100 / 5
    """

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
    """
    Detect whether the message is a calculator request.
    """

    text = text.strip().lower()

    patterns = [
        r"^calculate\s+[\d\s+\-*/().]+$",
        r"^compute\s+[\d\s+\-*/().]+$",
        r"^คำนวณ\s+[\d\s+\-*/().]+$",

        # Pure mathematical expressions
        r"^[\d\s+\-*/().]+$",

        # Natural language multiplication
        r"^what\s+is\s+[\d\s+\-*/().]+[?]?$",
    ]

    return any(
        re.match(pattern, text)
        for pattern in patterns
    )


def calculate(expression: str):
    """
    Safely evaluate a mathematical expression using AST.
    """

    node = ast.parse(
        expression,
        mode="eval",
    ).body

    return _evaluate(node)


def _evaluate(node):
    if isinstance(node, ast.Constant):

        if isinstance(
            node.value,
            (int, float),
        ):
            return node.value

        raise ValueError(
            "Invalid number"
        )

    if isinstance(node, ast.BinOp):

        operator = OPERATORS.get(
            type(node.op)
        )

        if operator is None:
            raise ValueError(
                "Unsupported operator"
            )

        return operator(
            _evaluate(node.left),
            _evaluate(node.right),
        )

    if isinstance(node, ast.UnaryOp):

        operator = OPERATORS.get(
            type(node.op)
        )

        if operator is None:
            raise ValueError(
                "Unsupported operator"
            )

        return operator(
            _evaluate(node.operand)
        )

    raise ValueError(
        "Invalid expression"
    )


# ============================================================
# Router
# ============================================================

class Router:

    def route(self, text: str) -> str:
        """
        Decide which subsystem should handle the request.

        Returns:

            tool:calculator
            search
            memory_llm
        """

        text = text.strip()
        t = text.lower()

        # ----------------------------------------------------
        # 1. Calculator
        # ----------------------------------------------------

        if is_calculation(text):
            return "tool:calculator"

        # ----------------------------------------------------
        # 2. Search
        # ----------------------------------------------------

        search_words = [
            "latest",
            "today",
            "current",
            "news",
            "ราคา",
            "ล่าสุด",
            "วันนี้",
            "ตอนนี้",
            "ค้นหา",
            "หาข้อมูล",
        ]

        if any(
            word in t
            for word in search_words
        ):
            return "search"

        # ----------------------------------------------------
        # 3. Default
        # ----------------------------------------------------

        return "memory_llm"