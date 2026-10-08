import numpy as np

from models import CanonicalForm, LinearProgram, Solution, TableSnapshot


class SimplexTableau:
    """Сокращённая симплекс-таблица со строкой цели (r, −Q)"""

    def __init__(self, form: CanonicalForm, tolerance: float):
        """Создаёт начальную симплекс-таблицу

        :param form: Каноническая постановка задачи
        :param tolerance: Числовой допуск
        :return: None
        """
        self.basis = list(form.basis)
        self.nonbasis = [j for j in range(len(form.c)) if j not in self.basis]
        self.tolerance = tolerance
        self.values = np.zeros((len(form.b) + 1, len(self.nonbasis) + 1))

        # При построении выбранные базисные столбцы уже образуют единичную матрицу
        self.values[:-1, :-1] = form.A[:, self.nonbasis]
        self.values[:-1, -1] = form.b

    def set_objective(self, costs, constant=0.0):
        """Пересчитывает строку цели для текущего базиса

        :param costs: Коэффициенты минимизируемой цели
        :param constant: Свободный член цели
        :return: None
        """
        basic_costs = costs[self.basis]
        self.values[-1, :-1] = costs[self.nonbasis] - basic_costs @ self.values[:-1, :-1]
        self.values[-1, -1] = -(constant + basic_costs @ self.values[:-1, -1])

    def pivot(self, row, column):
        """Обменивает базисную и свободную переменные

        :param row: Индекс разрешающей строки
        :param column: Индекс разрешающего столбца
        :return: None
        """
        old = self.values.copy()
        alpha = old[row, column]

        # Правило прямоугольника для всех обычных элементов, включая строку цели и b
        self.values = old - np.outer(old[:, column], old[row, :]) / alpha
        self.values[row, :] = old[row, :] / alpha
        self.values[:, column] = -old[:, column] / alpha
        self.values[row, column] = 1 / alpha

        self.basis[row], self.nonbasis[column] = self.nonbasis[column], self.basis[row]

    def drop_column(self, column):
        """Удаляет столбец свободной переменной

        :param column: Позиция столбца в таблице
        :return: None
        """
        self.values = np.delete(self.values, column, axis=1)
        self.nonbasis.pop(column)

    def drop_row(self, row):
        """Удаляет избыточное ограничение

        :param row: Позиция строки в таблице
        :return: None
        """
        self.values = np.delete(self.values, row, axis=0)
        self.basis.pop(row)


class TwoPhaseSimplex:
    """Двухфазный симплекс-метод с историей таблиц"""

    form: CanonicalForm
    table: SimplexTableau

    def __init__(self, tolerance=1e-9, max_iterations=1000, pivot_rule="bland"):
        """Настраивает точность и правило выбора переменной

        :param tolerance: Допуск для сравнений
        :param max_iterations: Общий лимит обменов
        :param pivot_rule: bland или most-negative
        :return: None
        """
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        if pivot_rule not in {"bland", "most-negative"}:
            raise ValueError("Правило выбора: bland или most-negative.")
        self.pivot_rule = pivot_rule
        self.history: list[TableSnapshot] = []
        self.iterations = 0

    def _remember(self, phase, action):
        """Сохраняет снимок текущей таблицы

        :param phase: Фаза I или II
        :param action: Описание выполненного шага
        :return: None
        """
        self.history.append(TableSnapshot(
            phase, action,
            [self.form.names[j] for j in self.table.basis],
            [self.form.names[j] for j in self.table.nonbasis],
            self.table.values.copy(),
        ))

    def _optimize(self, phase):
        """Выполняет симплекс-итерации текущей фазы

        :param phase: Фаза I или II
        :return: Статус optimal, unbounded или iteration-limit
        """
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
                column = min(candidates, key=lambda j: (self.table.values[-1, j], self.table.nonbasis[j]))

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
        """Решает задачу и восстанавливает исходные переменные

        :param problem: Исходная постановка задачи
        :return: Статус, оптимальная точка, значение цели и число обменов
        """
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
            # Сумма неотрицательных искусственных переменных не может уходить в минус бесконечность
            raise ArithmeticError("Численная ошибка в фазе I; проверьте масштаб коэффициентов.")
        if -self.table.values[-1, -1] > self.tolerance:
            return Solution("infeasible", iterations=self.iterations)

        # Нулевая искусственная переменная может остаться базисной при вырождении
        for row in range(len(self.table.basis) - 1, -1, -1):
            if self.table.basis[row] not in self.form.artificial:
                continue
            candidates = [
                j for j, index in enumerate(self.table.nonbasis)
                if index not in self.form.artificial
                   and abs(self.table.values[row, j]) > self.tolerance
            ]
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
