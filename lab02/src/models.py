from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Point:
    """Верхняя вершина: аргумент и вычисленное значение функции."""

    x: float
    y: float


@dataclass(frozen=True)
class Iteration:
    """Новая точка и значение предыдущей миноранты до обновления."""

    number: int
    point: Point
    lower: float
    gap: float


@dataclass
class Solution:
    """Результат поиска; точность условна относительно оценённого L."""

    status: Literal["converged", "iteration-limit", "invalid-lipschitz", "stalled"]
    point: Point
    lipschitz: float
    history: list[Iteration]
    points: list[Point]
    estimation_evaluations: int
    search_evaluations: int
    elapsed: float

