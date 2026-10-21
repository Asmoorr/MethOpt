from pathlib import Path
import sys

from config import Settings
from console_tables import print_solution
from expression import Expression
from piyavsky import PiyavskySolver
from plotting import save_plot


def main() -> int:
    """Запускает лабораторную с настройками lab02/.env."""
    directory = Path(__file__).resolve().parents[1]
    # UTF-8 сохраняет русские подписи и математические индексы при перенаправлении.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        settings = Settings.read(directory / ".env")
        function = Expression(settings.expression)
        result = PiyavskySolver().solve(
            function, settings.a, settings.b, settings.eps,
            settings.estimation_intervals, settings.max_iterations,
        )
        print_solution(result)
        destination = directory / "imgs" / "solution.png"
        save_plot(function, settings.expression, result, destination)
        print(f"График: {destination}")
        return 0 if result.status == "converged" else 1
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

