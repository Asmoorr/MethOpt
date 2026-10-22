import ast
import math


FUNCTIONS = {name: getattr(math, name) for name in (
    "sin", "cos", "tan", "exp", "log", "log10", "sqrt", "sinh", "cosh", "tanh"
)}
FUNCTIONS["abs"] = abs
CONSTANTS = {"pi": math.pi, "e": math.e}
ALLOWED_NAMES = {"x", *FUNCTIONS, *CONSTANTS}
ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp, ast.UnaryOp,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.UAdd, ast.USub,
    ast.Name, ast.Constant, ast.Load,
)


class Expression:
    """Математическое выражение с одной переменной и разрешёнными операциями."""

    def __init__(self, source: str):
        """Проверяет синтаксис выражения и компилирует его

        :param source: Выражение с x, разрешёнными функциями и константами
        :return: None
        """
        if len(source) > 1000:
            raise ValueError("Слишком длинное выражение функции.")
        try:
            tree = ast.parse(source, mode="eval")
        except SyntaxError as error:
            raise ValueError("Некорректная запись FUNCTION.") from error
        for node in ast.walk(tree):
            self._validate_node(node)

        self.code = compile(tree, "<function>", "eval")

    def _validate_node(self, node: ast.AST) -> None:
        """Проверяет один элемент синтаксического дерева

        :param node: Операция, имя, число или вызов функции
        :return: None
        """
        if isinstance(node, ast.Call):
            self._validate_call(node)
            return

        if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
            raise ValueError(f"Неизвестное имя: {node.id}")

        if isinstance(node, ast.Constant) and type(node.value) not in (int, float):
            raise ValueError("В выражении разрешены только числа.")

        if not isinstance(node, ALLOWED_NODES):
            raise ValueError(f"Недопустимая операция: {type(node).__name__}")

    def _validate_call(self, node: ast.Call) -> None:
        """Проверяет имя функции и единственный позиционный аргумент

        :param node: Вызов функции в выражении
        :return: None
        """
        if not isinstance(node.func, ast.Name):
            raise ValueError("Функцию нужно вызывать по имени, например sin(x).")

        if node.func.id not in FUNCTIONS:
            raise ValueError(f"Недопустимая функция: {node.func.id}")

        if len(node.args) != 1 or node.keywords:
            raise ValueError("Функция должна иметь один позиционный аргумент.")

    def __call__(self, x: float) -> float:
        """Вычисляет выражение в заданной точке

        :param x: Аргумент функции
        :return: Конечное вещественное значение выражения
        """
        variables = {**FUNCTIONS, **CONSTANTS, "x": x}
        try:
            value = float(eval(self.code, {"__builtins__": {}}, variables))
        except (ArithmeticError, ValueError, TypeError) as error:
            raise ValueError(f"Функция не определена как вещественное число при x={x:g}.") from error
        if not math.isfinite(value):
            raise ValueError(f"Получено бесконечное значение функции при x={x:g}.")
        return value

