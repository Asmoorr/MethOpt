from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class LinearProgram:
    """Исходная задача линейного программирования

    :param c: Коэффициенты целевой функции
    :param A: Матрица ограничений
    :param b: Правые части ограничений
    :param signs: Знаки ограничений: <=, >= или =
    :param sense: Направление оптимизации: min или max
    :param bounds: Границы переменных; по умолчанию (0, None)
    """

    c: np.ndarray
    A: np.ndarray
    b: np.ndarray
    signs: list[str]
    sense: Literal["min", "max"] = "min"
    bounds: list[tuple[float | None, float | None]] | None = None

    def __post_init__(self):
        """Преобразует входные данные в массивы и проверяет их согласованность

        :return: None
        """
        self.c = np.asarray(self.c, dtype=float).reshape(-1)
        self.b = np.asarray(self.b, dtype=float).reshape(-1)
        self.A = np.asarray(self.A, dtype=float).reshape(len(self.b), len(self.c))

        if len(self.signs) != len(self.b) or any(s not in {"<=", ">=", "="} for s in self.signs):
            raise ValueError("Для каждого ограничения укажите знак <=, >= или =.")
        if self.sense not in {"min", "max"}:
            raise ValueError("Направление оптимизации: min или max.")
        if self.bounds is None:
            self.bounds = [(0, None)] * len(self.c)
        elif len(self.bounds) != len(self.c):
            raise ValueError("Число пар bounds должно совпадать с числом переменных.")


@dataclass
class CanonicalForm:
    """Каноническая задача минимизации с начальным базисом

    :param A: Матрица равенств
    :param b: Правые части равенств
    :param c: Коэффициенты преобразованной цели
    :param constant: Свободный член цели
    :param basis: Индексы базисных переменных
    :param artificial: Индексы искусственных переменных
    :param names: Имена переменных
    :param shift: Сдвиг исходных переменных
    :param transform: Матрица замены x = shift + transform @ y
    """

    A: np.ndarray
    b: np.ndarray
    c: np.ndarray
    constant: float
    basis: list[int]
    artificial: set[int]
    names: list[str]
    shift: np.ndarray
    transform: np.ndarray

    @classmethod
    def from_problem(cls, problem: LinearProgram):
        """Приводит исходную задачу к каноническому виду

        :param problem: Исходная постановка задачи
        :return: Каноническая форма с базисом вспомогательной задачи
        """
        n = len(problem.c)
        shift = np.zeros(n)
        columns, names, upper_constraints = [], [], []

        for j, (lower, upper) in enumerate(problem.bounds):
            unit = np.eye(n)[:, j]
            if lower is not None:
                shift[j] = lower
                columns.append(unit)
                names.append(f"x{j + 1}" if lower == 0 else f"y{j + 1}")
                if upper is not None:
                    upper_constraints.append((len(columns) - 1, upper - lower))
            elif upper is not None:
                shift[j] = upper
                columns.append(-unit)
                names.append(f"y{j + 1}")
            else:
                columns.extend([unit, -unit])
                names.extend([f"x{j + 1}+", f"x{j + 1}-"])

        transform = np.column_stack(columns)
        A = problem.A @ transform
        b = problem.b - problem.A @ shift
        signs = list(problem.signs)

        for index, upper in upper_constraints:
            row = np.zeros(transform.shape[1])
            row[index] = 1
            A = np.vstack([A, row])
            b = np.append(b, upper)
            signs.append("<=")

        # Неотрицательная правая часть нужна для допустимого начального базиса.
        for i in range(len(b)):
            if b[i] < 0:
                A[i] *= -1
                b[i] *= -1
                signs[i] = {"<=": ">=", ">=": "<=", "=": "="}[signs[i]]

        direction = 1 if problem.sense == "min" else -1
        c = direction * (problem.c @ transform)
        constant = float(direction * (problem.c @ shift))
        basis, artificial = [], set()

        def add_column(i, value, artificial_column=False):
            """Добавляет дополнительную или искусственную переменную

            :param i: Индекс ограничения
            :param value: Коэффициент нового столбца в строке i
            :param artificial_column: Признак искусственной переменной
            :return: Индекс добавленного столбца
            """
            nonlocal A, c
            column = np.zeros(len(b))
            column[i] = value
            A = np.column_stack([A, column])
            c = np.append(c, 0)
            index = A.shape[1] - 1
            names.append(("a" if artificial_column else "s") + str(i + 1))
            if artificial_column:
                artificial.add(index)
            return index

        for i, sign in enumerate(signs):
            if sign == "<=":
                basis.append(add_column(i, 1))
            else:
                if sign == ">=":
                    add_column(i, -1)
                basis.append(add_column(i, 1, artificial_column=True))

        return cls(A, b, c, constant, basis, artificial, names, shift, transform)


@dataclass
class TableSnapshot:
    """Снимок симплекс-таблицы для вывода шагов

    :param phase: Фаза I или II
    :param action: Описание шага
    :param basis: Имена базисных переменных
    :param nonbasis: Имена свободных переменных
    :param values: Коэффициенты таблицы, правые части и строка цели
    """
    phase: str
    action: str
    basis: list[str]
    nonbasis: list[str]
    values: np.ndarray


@dataclass
class Solution:
    """Результат решения исходной задачи

    :param status: optimal, infeasible, unbounded или iteration-limit
    :param x: Оптимальная точка; None, если оптимум не найден
    :param value: Значение цели в оптимуме или None
    :param iterations: Число выполненных обменов
    """
    status: Literal["optimal", "infeasible", "unbounded", "iteration-limit"]
    x: np.ndarray | None = None
    value: float | None = None
    iterations: int = 0
