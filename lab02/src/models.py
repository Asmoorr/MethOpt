from collections.abc import Callable
from math import isfinite
from dataclasses import dataclass
from typing import Literal


@dataclass
class OptimizationProblem:
    """Исходная задача минимизации на отрезке

    :param function: Вычисляемая функция одной переменной
    :param a: Левая граница отрезка
    :param b: Правая граница отрезка
    """

    function: Callable[[float], float]
    a: float
    b: float

    def __post_init__(self):
        """Проверяет конечность и порядок границ

        :return: None
        """
        if not all(isfinite(value) for value in (self.a, self.b, self.b - self.a)):
            raise ValueError("Границы и длина отрезка должны быть конечными.")
        if self.a >= self.b:
            raise ValueError("Требуется a < b.")

    def evaluate(self, x: float) -> "Point":
        """Вычисляет вещественное конечное значение функции

        :param x: Аргумент функции
        :return: Точка графика функции
        """
        value = float(self.function(x))
        if not isfinite(value):
            raise ValueError(f"Неконечное значение функции при x={x:g}.")
        return Point(x, value)


@dataclass(frozen=True)
class Point:
    """Точка графика функции или вершина миноранты

    :param x: Координата по оси аргумента
    :param y: Значение функции или миноранты
    """

    x: float
    y: float


@dataclass(frozen=True)
class Iteration:
    """Снимок одной завершённой итерации

    :param number: Номер новой точки после двух стартовых
    :param point: Вычисленная точка исходной функции
    :param lower: Значение предыдущей миноранты в новой точке
    :param gap: Разность point.y - lower до обновления миноранты
    """

    number: int
    point: Point
    lower: float
    gap: float


@dataclass
class Solution:
    """Результат поиска с историей и данными для визуализации

    :param status: converged, iteration-limit, invalid-lipschitz или stalled
    :param point: Лучшая принятая точка, включая границы
    :param lipschitz: Однократно оценённая константа L
    :param history: Снимки завершённых итераций
    :param points: Принятые верхние вершины в порядке возрастания x
    :param estimation_evaluations: Число вычислений для оценки L, включая границы
    :param search_evaluations: Дополнительные вычисления при поиске
    :param elapsed: Время оценки L и поиска в секундах без вывода и графиков
    """

    status: Literal["converged", "iteration-limit", "invalid-lipschitz", "stalled"]
    point: Point
    lipschitz: float
    history: list[Iteration]
    points: list[Point]
    estimation_evaluations: int
    search_evaluations: int
    elapsed: float

