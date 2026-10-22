from pathlib import Path
import sys

from rich.console import Console
from rich.text import Text

from models import OptimizationProblem
from config import Settings
from console_tables import print_solution
from expression import Expression
from piyavsky import PiyavskySolver
from plotting import save_plot


def main() -> int:
    """Запускает расчёт, вывод таблицы и сохранение графика

    :return: 0 при достижении точности, 1 при ошибке или досрочной остановке
    """
    directory = Path(__file__).resolve().parents[1]
    # UTF-8 сохраняет русские подписи и математические индексы при перенаправлении.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        settings = Settings.read(directory / ".env")
        function = Expression(settings.expression)
        problem = OptimizationProblem(function=function, a=settings.a, b=settings.b)
        solver = PiyavskySolver(
            tolerance=settings.eps,
            estimation_intervals=settings.estimation_intervals,
            max_iterations=settings.max_iterations,
        )
        result = solver.solve(problem)

        print_solution(result)
        destination = directory / "imgs" / "solution.png"
        save_plot(function, settings.expression, result, destination)
        Console().print(Text.assemble("График: ", (str(destination), "bright_cyan")))
        return 0 if result.status == "converged" else 1
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

