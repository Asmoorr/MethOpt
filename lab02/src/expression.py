import ast
import math


FUNCTIONS = {name: getattr(math, name) for name in (
    "sin", "cos", "tan", "exp", "log", "log10", "sqrt", "sinh", "cosh", "tanh"
)}
FUNCTIONS["abs"] = abs
CONSTANTS = {"pi": math.pi, "e": math.e}


class Expression:
    """Математическое выражение с одной переменной и разрешёнными операциями."""

    def __init__(self, source: str):
        if len(source) > 1000:
            raise ValueError("Слишком длинное выражение функции.")
        try:
            tree = ast.parse(source, mode="eval")
        except SyntaxError as error:
            raise ValueError("Некорректная запись FUNCTION.") from error
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub,
                   ast.Mult, ast.Div, ast.Pow, ast.UAdd, ast.USub, ast.Load)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (not isinstance(node.func, ast.Name)
                        or node.func.id not in FUNCTIONS
                        or len(node.args) != 1 or node.keywords):
                    raise ValueError("Разрешены только перечисленные функции одного аргумента.")
            elif isinstance(node, ast.Name):
                if node.id not in {"x", *FUNCTIONS, *CONSTANTS}:
                    raise ValueError(f"Неизвестное имя: {node.id}")
            elif isinstance(node, ast.Constant):
                if type(node.value) not in (int, float):
                    raise ValueError("В выражении разрешены только числа.")
            elif not isinstance(node, allowed):
                raise ValueError(f"Недопустимая операция: {type(node).__name__}")
        self.code = compile(tree, "<function>", "eval")

    def __call__(self, x: float) -> float:
        try:
            value = float(eval(self.code, {"__builtins__": {}},
                               {**FUNCTIONS, **CONSTANTS, "x": x}))
        except (ArithmeticError, ValueError, TypeError) as error:
            raise ValueError(f"Функция не определена как вещественное число при x={x:g}.") from error
        if not math.isfinite(value):
            raise ValueError(f"Получено бесконечное значение функции при x={x:g}.")
        return value

