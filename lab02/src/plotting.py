from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np

from models import Solution
from piyavsky import intersection


def _plot_function(axes: Axes, function: Callable[[float], float],
                   expression: str, result: Solution) -> None:
    """Рисует функцию, итоговую миноранту и найденный минимум

    :param axes: Область графика функции
    :param function: Вычисляемая исходная функция
    :param expression: Текст функции для заголовка
    :param result: Результат поиска с упорядоченными точками
    :return: None
    """
    points = result.points
    arguments = np.linspace(points[0].x, points[-1].x, 2001)
    values = [function(float(argument)) for argument in arguments]

    # Ломаная чередует принятые точки и пересечения соседних ветвей.
    vertices = [points[0]]
    for left, right in zip(points, points[1:]):
        lower_vertex = intersection(left, right, result.lipschitz)
        vertices.extend([lower_vertex, right])

    minorant_x = [vertex.x for vertex in vertices]
    minorant_y = [vertex.y for vertex in vertices]
    sampled_x = [point.x for point in points]
    sampled_y = [point.y for point in points]
    best = result.point
    best_label = f"Лучшая точка ({best.x:.6g}; {best.y:.6g})"

    axes.plot(arguments, values, label="Исходная функция", color="#164e83")
    axes.plot(minorant_x, minorant_y, label="Итоговая миноранта", color="#24936e", linewidth=1)
    axes.scatter(sampled_x, sampled_y, s=9, color="#164e83")
    axes.scatter(best.x, best.y, s=75, color="#cb4b33", zorder=5, label=best_label)

    title = f"Метод Пиявского: {expression}\nL = {result.lipschitz:.6g}; {result.status}"
    axes.set(title=title, xlabel="x", ylabel="f(x), p(x)")
    axes.legend()
    axes.grid(alpha=0.2)


def _plot_convergence(axes: Axes, result: Solution) -> None:
    """Рисует разрыв между функцией и минорантой по итерациям

    :param axes: Область графика сходимости
    :param result: Результат поиска с историей итераций
    :return: None
    """
    iterations = [step.number for step in result.history]
    gaps = [step.gap for step in result.history]
    axes.plot(iterations, gaps)

    if result.history:
        axes.set_yscale("symlog", linthresh=1e-10)

    axes.set(xlabel="Итерация", ylabel=r"$f(u_n) - p_{n-1}(u_n)$")
    axes.grid(alpha=0.2)


def save_plot(function: Callable[[float], float], expression: str,
              result: Solution, destination: Path) -> None:
    """Сохраняет функцию, миноранту и историю разрыва на одном рисунке

    :param function: Вычисляемая исходная функция
    :param expression: Текст функции для заголовка
    :param result: Результат поиска и принятые вершины
    :param destination: Путь сохранения PNG
    :return: None
    """
    figure, (function_axes, convergence_axes) = plt.subplots(
        2, 1,
        figsize=(11, 8),
        layout="constrained",
        gridspec_kw={"height_ratios": [3, 1]},
    )
    try:
        _plot_function(function_axes, function, expression, result)
        _plot_convergence(convergence_axes, result)
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160)
    finally:
        plt.close(figure)
