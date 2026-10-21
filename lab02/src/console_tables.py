from rich import box
from rich.console import Console
from rich.table import Table

from models import Solution


def print_solution(result: Solution) -> None:
    """Показывает историю поиска и отдельные счётчики оценки L и поиска."""
    console = Console()
    table = Table(title="Метод Пиявского", box=box.ROUNDED,
                  header_style="bold cyan", border_style="dim")
    for title in ("Шаг", "uₙ", "f(uₙ)", "pₙ₋₁(uₙ)", "Разрыв"):
        table.add_column(title, justify="right")
    for step in result.history:
        table.add_row(str(step.number), *(f"{value:.9g}" for value in
                      (step.point.x, step.point.y, step.lower, step.gap)))
    console.print(table)
    console.print(f"Статус: {result.status}; L = {result.lipschitz:.12g}")
    console.print(f"Лучшая точка: x = {result.point.x:.12g}, f(x) = {result.point.y:.12g}")
    console.print(f"Завершённых итераций: {len(result.history)}; "
                  f"вычислений при поиске: {result.search_evaluations} (+2 граничные из оценки L)")
    console.print(f"Вычислений при оценке L: {result.estimation_evaluations}")
    console.print(f"Время оценки L и поиска: {result.elapsed:.6f} с")
    console.print("L оценено численно один раз с K=1.2; точность условна относительно этой оценки.")

