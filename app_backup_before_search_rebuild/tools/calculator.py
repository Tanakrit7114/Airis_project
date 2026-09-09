import ast
import operator


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression: str):
    tree = ast.parse(expression, mode="eval")
    return _evaluate(tree.body)


def _evaluate(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Invalid number")

    if isinstance(node, ast.BinOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported operator")

        return operation(
            _evaluate(node.left),
            _evaluate(node.right),
        )

    if isinstance(node, ast.UnaryOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported operator")

        return operation(_evaluate(node.operand))

    raise ValueError("Invalid expression")
