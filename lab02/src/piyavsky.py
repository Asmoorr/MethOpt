from collections.abc import Callable
from math import isfinite
from time import perf_counter

from models import Iteration, Point, Solution


def intersection(left: Point, right: Point, lipschitz: float) -> Point:
    """Нижняя вершина между соседними верхними вершинами."""
    width = right.x - left.x
    x = left.x + width / 2 + (left.y - right.y) / (2 * lipschitz)
    y = left.y / 2 + right.y / 2 - lipschitz * width / 2
    return Point(x, y)


class PiyavskySolver:
    """Метод ломаных с однократной оценкой L и историей новых точек."""

    def solve(self, function: Callable[[float], float], a: float, b: float,
              eps: float, estimation_intervals: int = 10000,
              max_iterations: int = 10000) -> Solution:
        if (not all(isfinite(v) for v in (a, b, eps, b-a)) or a >= b or eps <= 0
                or estimation_intervals < 2 or max_iterations < 1):
            raise ValueError("Некорректные параметры метода.")
        started = perf_counter()

        def evaluate(x: float) -> Point:
            y = float(function(x))
            if not isfinite(y):
                raise ValueError(f"Неконечное значение функции при x={x:g}.")
            return Point(x, y)

        # Сетка применяется только здесь: её внутренние точки не участвуют в поиске.
        first = previous = evaluate(a)
        largest_slope = 0.0
        for i in range(1, estimation_intervals + 1):
            current = evaluate(b if i == estimation_intervals else a + (b-a)*i/estimation_intervals)
            if current.x <= previous.x:
                raise ValueError("Шаг сетки слишком мал для машинной точности.")
            largest_slope = max(largest_slope, abs((current.y-previous.y)/(current.x-previous.x)))
            previous = current
        lipschitz = 1.2 * largest_slope
        # При нулевой оценке используем положительный наклон; постоянство не доказано сеткой.
        if lipschitz == 0:
            lipschitz = min(1.0, eps) / max(1.0, b-a)
        if not isfinite(lipschitz) or lipschitz <= 0:
            raise ValueError("Не удалось получить конечную положительную оценку L.")
        points = [first, previous]
        history = []
        best = min(points, key=lambda point: point.y)
        evaluations = 0
        status = "iteration-limit"
        for number in range(1, max_iterations + 1):
            candidates = [intersection(left, right, lipschitz)
                          for left, right in zip(points, points[1:])]
            index = min(range(len(candidates)), key=lambda i: (candidates[i].y, candidates[i].x))
            lower = candidates[index]
            left, right = points[index:index+2]
            if not left.x < lower.x < right.x:
                status = "stalled"
                break
            point = evaluate(lower.x)
            evaluations += 1
            # L не пересчитывается: обнаруженное нарушение завершает расчёт.
            slopes = (abs((point.y-left.y)/(point.x-left.x)),
                      abs((right.y-point.y)/(right.x-point.x)))
            if max(slopes) > lipschitz * (1 + 1e-10):
                status = "invalid-lipschitz"
                break
            gap = point.y - lower.y
            history.append(Iteration(number, point, lower.y, gap))
            points.insert(index+1, point)
            best = min(best, point, key=lambda item: item.y)
            # Сравниваем с ПРЕДЫДУЩЕЙ ломаной; после вставки разрыв в точке равен нулю.
            if gap < eps:
                status = "converged"
                break
        return Solution(status, best, lipschitz, history, points,
                        estimation_intervals+1, evaluations, perf_counter()-started)

