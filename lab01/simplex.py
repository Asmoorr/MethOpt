from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
import argparse

import numpy as np


@dataclass
class LinearProgram:
    """Постановка исходной задачи в естественных обозначениях."""

    c: np.ndarray
    A: np.ndarray
    b: np.ndarray
    signs: list[str]
    sense: Literal["min", "max"] = "min"
    bounds: list[tuple[float | None, float | None]] | None = None

    def __post_init__(self):
        self.c = np.asarray(self.c, dtype=float).reshape(-1)
        self.b = np.asarray(self.b, dtype=float).reshape(-1)
        self.A = np.asarray(self.A, dtype=float).reshape(len(self.b), len(self.c))
        if len(self.signs) != len(self.b) or any(s not in {"<=", ">=", "="} for s in self.signs):
            raise ValueError("Для каждого ограничения укажите знак <=, >= или =.")
        if self.sense not in {"min", "max"}:
            raise ValueError("Направление оптимизации: min или max.")
        if self.bounds is None:
            self.bounds = [(0, None)] * len(self.c)
        if len(self.bounds) != len(self.c):
            raise ValueError("Число пар bounds должно совпадать с числом переменных.")


@dataclass
class CanonicalForm:
    """Равенства с начальным базисом и преобразование x = shift + transform @ y."""

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
    phase: str
    action: str
    basis: list[str]
    nonbasis: list[str]
    values: np.ndarray


class SimplexTableau:
    """Сокращённая таблица: x_B + D @ x_N = b; W = Q + r @ x_N.

    Последняя строка содержит r и -Q, как в конспекте.
    При обмене меняются и числа, и названия строки/столбца.
    """

    def __init__(self, form: CanonicalForm, tolerance: float):
        self.basis = list(form.basis)
        self.nonbasis = [j for j in range(len(form.c)) if j not in self.basis]
        self.tolerance = tolerance
        self.values = np.zeros((len(form.b) + 1, len(self.nonbasis) + 1))
        # При построении выбранные базисные столбцы уже образуют единичную матрицу.
        self.values[:-1, :-1] = form.A[:, self.nonbasis]
        self.values[:-1, -1] = form.b

    def set_objective(self, costs, constant=0.0):
        basic_costs = costs[self.basis]
        self.values[-1, :-1] = costs[self.nonbasis] - basic_costs @ self.values[:-1, :-1]
        self.values[-1, -1] = -(constant + basic_costs @ self.values[:-1, -1])

    def pivot(self, row, column):
        old = self.values.copy()
        alpha = old[row, column]
        # Правило прямоугольника для всех обычных элементов, включая строку цели и b.
        self.values = old - np.outer(old[:, column], old[row, :]) / alpha
        self.values[row, :] = old[row, :] / alpha
        self.values[:, column] = -old[:, column] / alpha
        self.values[row, column] = 1 / alpha
        self.basis[row], self.nonbasis[column] = self.nonbasis[column], self.basis[row]

    def drop_column(self, column):
        self.values = np.delete(self.values, column, axis=1)
        self.nonbasis.pop(column)

    def drop_row(self, row):
        self.values = np.delete(self.values, row, axis=0)
        self.basis.pop(row)


@dataclass
class Solution:
    status: Literal["optimal", "infeasible", "unbounded", "iteration-limit"]
    x: np.ndarray | None = None
    value: float | None = None
    iterations: int = 0


class TwoPhaseSimplex:
    """Две фазы симплекс-метода с историей таблиц для разбора на защите."""

    def __init__(self, tolerance=1e-9, max_iterations=1000, pivot_rule="bland"):
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        if pivot_rule not in {"bland", "most-negative"}:
            raise ValueError("Правило выбора: bland или most-negative.")
        self.pivot_rule = pivot_rule
        self.history: list[TableSnapshot] = []
        self.iterations = 0

    def _remember(self, phase, action):
        self.history.append(TableSnapshot(
            phase, action,
            [self.form.names[j] for j in self.table.basis],
            [self.form.names[j] for j in self.table.nonbasis],
            self.table.values.copy(),
        ))

    def _optimize(self, phase):
        while True:
            candidates = np.flatnonzero(self.table.values[-1, :-1] < -self.tolerance)
            if not len(candidates):
                return "optimal"
            if self.iterations >= self.max_iterations:
                return "iteration-limit"
            if self.pivot_rule == "bland":
                # Наименьший индекс переменной, а не позиция переставленного столбца.
                column = min(candidates, key=lambda j: self.table.nonbasis[j])
            else:
                column = min(candidates, key=lambda j: (
                    self.table.values[-1, j], self.table.nonbasis[j]))
            eligible = np.flatnonzero(self.table.values[:-1, column] > self.tolerance)
            if not len(eligible):
                return "unbounded"
            ratios = self.table.values[eligible, -1] / self.table.values[eligible, column]
            minimum = ratios.min()
            tied = eligible[np.abs(ratios - minimum) <= self.tolerance]
            row = min(tied, key=lambda i: self.table.basis[i])
            entering = self.form.names[self.table.nonbasis[column]]
            leaving_id = self.table.basis[row]
            leaving = self.form.names[leaving_id]
            alpha = self.table.values[row, column]
            self.table.pivot(row, column)
            self.iterations += 1
            self._remember(phase, f"Входит {entering}, выходит {leaving}; элемент {alpha:g}")
            if leaving_id in self.form.artificial:
                self.table.drop_column(column)
                self._remember(phase, f"Удалён столбец искусственной переменной {leaving}")

    def solve(self, problem: LinearProgram) -> Solution:
        self.history = []
        self.iterations = 0
        self.form = CanonicalForm.from_problem(problem)
        self.table = SimplexTableau(self.form, self.tolerance)
        auxiliary_costs = np.zeros(len(self.form.c))
        auxiliary_costs[list(self.form.artificial)] = 1
        self.table.set_objective(auxiliary_costs)
        self._remember("I", "Начальная таблица вспомогательной задачи")
        status = self._optimize("I")
        if status == "iteration-limit":
            return Solution(status, iterations=self.iterations)
        if status == "unbounded":
            # Сумма неотрицательных искусственных переменных не может уходить в -inf.
            raise ArithmeticError("Численная ошибка в фазе I; проверьте масштаб коэффициентов.")
        if -self.table.values[-1, -1] > self.tolerance:
            return Solution("infeasible", iterations=self.iterations)

        # Нулевая искусственная переменная может остаться базисной при вырождении.
        for row in range(len(self.table.basis) - 1, -1, -1):
            if self.table.basis[row] not in self.form.artificial:
                continue
            candidates = [j for j, index in enumerate(self.table.nonbasis)
                          if index not in self.form.artificial
                          and abs(self.table.values[row, j]) > self.tolerance]
            if candidates:
                if self.iterations >= self.max_iterations:
                    return Solution("iteration-limit", iterations=self.iterations)
                column = min(candidates, key=lambda j: self.table.nonbasis[j])
                self.table.pivot(row, column)
                self.iterations += 1
                self.table.drop_column(column)
                self._remember("I", "Выведена нулевая искусственная переменная")
            else:
                self.table.drop_row(row)
                self._remember("I", "Удалено избыточное равенство 0 = 0")
        for column in range(len(self.table.nonbasis) - 1, -1, -1):
            if self.table.nonbasis[column] in self.form.artificial:
                self.table.drop_column(column)

        self.table.set_objective(self.form.c, self.form.constant)
        self._remember("II", "Возвращение к основной целевой функции")
        status = self._optimize("II")
        if status != "optimal":
            return Solution(status, iterations=self.iterations)
        canonical_x = np.zeros(len(self.form.c))
        canonical_x[self.table.basis] = self.table.values[:-1, -1]
        y = canonical_x[:self.form.transform.shape[1]]
        x = self.form.shift + self.form.transform @ y
        return Solution("optimal", x, float(problem.c @ x), self.iterations)

    def print_steps(self):
        def number(value):
            return str(Fraction(float(value)).limit_denominator(10000))

        for step in self.history:
            print(f"\nФаза {step.phase}. {step.action}")
            rows = [["Базис", *step.nonbasis, "b / -Q"]]
            rows += [[name, *(number(v) for v in values)]
                     for name, values in zip([*step.basis, "Цель"], step.values)]
            widths = [max(len(row[j]) for row in rows) for j in range(len(rows[0]))]
            for row in rows:
                print(" | ".join(cell.rjust(width) for cell, width in zip(row, widths)))


def check_with_scipy(problem: LinearProgram, solution: Solution):
    """Независимая проверка исходной постановки; не используется внутри алгоритма."""
    from scipy.optimize import linprog

    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for row, rhs, sign in zip(problem.A, problem.b, problem.signs):
        if sign == "=":
            A_eq.append(row)
            b_eq.append(rhs)
        else:
            factor = 1 if sign == "<=" else -1
            A_ub.append(factor * row)
            b_ub.append(factor * rhs)
    direction = 1 if problem.sense == "min" else -1
    reference = linprog(
        direction * problem.c,
        A_ub=np.array(A_ub) if A_ub else None, b_ub=np.array(b_ub) if b_ub else None,
        A_eq=np.array(A_eq) if A_eq else None, b_eq=np.array(b_eq) if b_eq else None,
        bounds=problem.bounds, method="highs",
    )
    reference_status = {0: "optimal", 2: "infeasible", 3: "unbounded"}.get(reference.status, "other")
    matches = solution.status == reference_status
    if solution.status == reference_status == "optimal":
        # При нескольких оптимумах точки могут отличаться: сравниваем значение и допустимость.
        lhs = problem.A @ solution.x
        feasible = all((v <= rhs + 1e-7 if sign == "<=" else
                        v >= rhs - 1e-7 if sign == ">=" else abs(v - rhs) <= 1e-7)
                       for v, rhs, sign in zip(lhs, problem.b, problem.signs))
        feasible &= all((lo is None or x >= lo - 1e-7) and (hi is None or x <= hi + 1e-7)
                        for x, (lo, hi) in zip(solution.x, problem.bounds))
        matches = feasible and np.isclose(solution.value, direction * reference.fun, atol=1e-7, rtol=1e-7)
    return reference, bool(matches)


def main():
    parser = argparse.ArgumentParser(description="Учебный двухфазный симплекс-метод")
    parser.add_argument("--quiet", action="store_true", help="Не печатать промежуточные таблицы")
    parser.add_argument("--no-scipy", action="store_true", help="Не сравнивать с SciPy")
    args = parser.parse_args()
    # Вариант 11. Здесь можно задать другую ЗЛП любого размера.
    problem = LinearProgram(
        c=[1, 2, 4, 1],
        A=[[1, 1, 1, 0], [0, 1, 2, 1], [1, 0, 0, 1]],
        b=[10, 6, 2], signs=["<=", "=", ">="], sense="max",
    )
    # Для похожей на конспект последовательности выбираем наиболее отрицательный коэффициент.
    # В общем случае правило Бланда (по умолчанию) защищает от зацикливания.
    solver = TwoPhaseSimplex(pivot_rule="most-negative")
    solution = solver.solve(problem)
    if not args.quiet:
        print("s — дополнительная переменная, a — искусственная; Цель: коэффициенты и -Q.")
        solver.print_steps()
    descriptions = {
        "optimal": "Оптимальное решение найдено",
        "infeasible": "Область допустимых решений пуста",
        "unbounded": "Целевая функция не ограничена в направлении оптимизации",
        "iteration-limit": "Достигнут предел итераций; вывод об оптимальности не сделан",
    }
    print(f"\n{descriptions[solution.status]}. Итераций: {solution.iterations}")
    if solution.x is not None:
        print("x* =", np.round(solution.x, 8))
        print(f"Целевая функция = {solution.value:.8g}")
    if not args.no_scipy:
        try:
            reference, matches = check_with_scipy(problem, solution)
            print("Проверка SciPy:", "совпадает" if matches else "НЕ совпадает")
            if reference.success:
                print("SciPy x* =", np.round(reference.x, 8))
                print(f"SciPy: целевая функция = {problem.c @ reference.x:.8g}")
        except ImportError:
            print("Проверка SciPy не выполнена. Установите: python -m pip install scipy")


if __name__ == "__main__":
    main()
