from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from models import Solution


def print_solution(result: Solution) -> None:
    """Показывает историю поиска и итоговые показатели

    :param result: Результат решения с историей итераций
    :return: None
    """
    console = Console()
    table = Table(
        title="Метод Пиявского",
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="dim",
    )
    for title in ("Шаг", "uₙ", "f(uₙ)", "pₙ₋₁(uₙ)", "Разрыв"):
        table.add_column(title, justify="right")

    for step in result.history:
        values = (step.point.x, step.point.y, step.lower, step.gap)
        table.add_row(str(step.number), *(f"{value:.9g}" for value in values))

    console.print(table)
    console.print(Text.assemble("Статус: ", (result.status, "bright_cyan")))
    console.print(Text.assemble(
        "Найденный минимум: ",
        (f"x = {result.point.x:.12g}, ", "bright_cyan"),
        ("f", "magenta"),
        (f"(x) = {result.point.y:.12g}", "bright_cyan"),
    ))
    console.print(Text.assemble("Число итераций: ", (str(len(result.history)), "bright_cyan")))
    console.print(Text.assemble("Время расчётов: ", (f"{result.elapsed:.6f} с", "bright_cyan")))


