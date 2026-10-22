from math import isfinite
from time import perf_counter

from models import Iteration, OptimizationProblem, Point, Solution


def intersection(left: Point, right: Point, lipschitz: float) -> Point:
    """Вычисляет нижнюю вершину между соседними верхними вершинами

    :param left: Верхняя вершина слева
    :param right: Верхняя вершина справа
    :param lipschitz: Положительная константа наклона L
    :return: Точка пересечения ветвей миноранты
    """
    width = right.x - left.x
    midpoint = left.x + width / 2
    correction = (left.y - right.y) / (2 * lipschitz)
    lower_value = left.y / 2 + right.y / 2 - lipschitz * width / 2
    return Point(midpoint + correction, lower_value)


class PiyavskySolver:
    """Метод ломаных с фиксированной оценкой L и историей итераций"""

    def __init__(self, tolerance=0.01, estimation_intervals=10000, max_iterations=10000):
        """Настраивает точность и ограничения вычислений

        :param tolerance: Положительная точность по значению функции
        :param estimation_intervals: Число интервалов сетки для оценки L
        :param max_iterations: Максимальное число новых точек поиска
        :return: None
        """
        if not isfinite(tolerance) or tolerance <= 0:
            raise ValueError("Точность должна быть положительной и конечной.")
        if type(estimation_intervals) is not int or estimation_intervals < 2:
            raise ValueError("Число интервалов должно быть целым и не меньше 2.")
        if type(max_iterations) is not int or max_iterations < 1:
            raise ValueError("Лимит итераций должен быть положительным целым числом.")
        self.tolerance = tolerance
        self.estimation_intervals = estimation_intervals
        self.max_iterations = max_iterations

    def _estimate_lipschitz(self, problem: OptimizationProblem):
        """Один раз оценивает L по сетке с коэффициентом запаса 1.2

        :param problem: Исходная задача минимизации
        :return: Оценка L и две стартовые точки на границах отрезка
        """
        first = problem.evaluate(problem.a)
        previous = first
        width = problem.b - problem.a
        largest_slope = 0.0

        for i in range(1, self.estimation_intervals + 1):
            x = problem.a + width * i / self.estimation_intervals
            if i == self.estimation_intervals:
                x = problem.b
            current = problem.evaluate(x)
            delta_x = current.x - previous.x
            delta_y = current.y - previous.y

            slope = abs(delta_y / delta_x)
            largest_slope = max(largest_slope, slope)
            previous = current

        lipschitz = 1.2 * largest_slope

        if lipschitz == 0:
            lipschitz = min(1.0, self.tolerance) / max(1.0, width)
        if not isfinite(lipschitz) or lipschitz <= 0:
            raise ValueError("Не удалось получить конечную положительную оценку L.")
        return lipschitz, [first, previous]

    def _optimize(self, problem: OptimizationProblem, lipschitz: float, points: list[Point]):
        """Уточняет миноранту до выполнения критерия точности или остановки

        :param problem: Исходная задача
        :param lipschitz: Фиксированная оценка L
        :param points: Верхние вершины; список обновляется при поиске
        :return: Статус, лучшая точка, история и число новых вычислений
        """
        history = []
        best = min(points, key=lambda point: point.y)
        evaluations = 0
        status = "iteration-limit"

        for number in range(1, self.max_iterations + 1):
            candidates = [
                intersection(left, right, lipschitz)
                for left, right in zip(points, points[1:])
            ]
            index = min(
                range(len(candidates)),
                key=lambda i: (candidates[i].y, candidates[i].x),
            )
            lower = candidates[index]
            left, right = points[index:index + 2]
            if not left.x < lower.x < right.x:
                status = "stalled"
                break

            point = problem.evaluate(lower.x)
            evaluations += 1
            left_slope = abs((point.y - left.y) / (point.x - left.x))
            right_slope = abs((right.y - point.y) / (right.x - point.x))

            if max(left_slope, right_slope) > lipschitz * (1 + 1e-10):
                status = "invalid-lipschitz"
                break

            gap = point.y - lower.y
            history.append(Iteration(number, point, lower.y, gap))
            points.insert(index + 1, point)
            if point.y < best.y:
                best = point

            if gap < self.tolerance:
                status = "converged"
                break

        return status, best, history, evaluations

    def solve(self, problem: OptimizationProblem) -> Solution:
        """Оценивает L, запускает поиск и собирает результат

        :param problem: Функция и отрезок минимизации
        :return: Ответ, история, счётчики вычислений и время расчёта
        """
        started = perf_counter()
        lipschitz, points = self._estimate_lipschitz(problem)
        status, best, history, evaluations = self._optimize(problem, lipschitz, points)
        elapsed = perf_counter() - started

        return Solution(
            status=status,
            point=best,
            lipschitz=lipschitz,
            history=history,
            points=points,
            estimation_evaluations=self.estimation_intervals + 1,
            search_evaluations=evaluations,
            elapsed=elapsed,
        )
