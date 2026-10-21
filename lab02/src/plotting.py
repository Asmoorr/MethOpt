from collections.abc import Callable
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from models import Solution
from piyavsky import intersection


def save_plot(function: Callable[[float], float], expression: str,
              result: Solution, destination: Path) -> None:
    """Рисует функцию по сетке, а ломаную — непосредственно по её вершинам."""
    points = result.points
    xs = np.linspace(points[0].x, points[-1].x, 2001)
    vertices = [points[0]]
    for left, right in zip(points, points[1:]):
        vertices.extend([intersection(left, right, result.lipschitz), right])
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), layout="constrained",
                             gridspec_kw={"height_ratios": [3, 1]})
    ax, convergence = axes
    ax.plot(xs, [function(float(x)) for x in xs], label="Исходная функция", color="#164e83")
    ax.plot([p.x for p in vertices], [p.y for p in vertices],
            label="Итоговая миноранта", color="#24936e", linewidth=1)
    ax.scatter([p.x for p in points], [p.y for p in points], s=9, color="#164e83")
    ax.scatter(result.point.x, result.point.y, s=75, color="#cb4b33", zorder=5,
               label=f"Лучшая точка ({result.point.x:.6g}; {result.point.y:.6g})")
    ax.set(title=f"Метод Пиявского: {expression}\nL ≈ {result.lipschitz:.6g}; {result.status}",
           xlabel="x", ylabel="f(x), p(x)")
    ax.legend()
    ax.grid(alpha=0.2)
    if result.history:
        convergence.plot([s.number for s in result.history], [s.gap for s in result.history])
        convergence.set_yscale("symlog", linthresh=1e-10)
    convergence.set(xlabel="Итерация", ylabel="f(uₙ) − pₙ₋₁(uₙ)")
    convergence.grid(alpha=0.2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=160)
    plt.close(fig)

