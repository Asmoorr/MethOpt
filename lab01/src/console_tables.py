from fractions import Fraction
from math import isclose
from typing import TYPE_CHECKING, Iterable

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from models import TableSnapshot


class ConsoleTablePrinter:
    """Вывод симплекс-таблиц в консоль через Rich"""

    def __init__(self, console: Console | None = None):
        """Настраивает консоль для вывода таблиц

        :param console: Консоль Rich; по умолчанию создаётся новая
        :return: None
        """
        self.console = console if console is not None else Console()

    @staticmethod
    def format_number(value: float) -> str:
        """Форматирует число как дробь или десятичную запись

        :param value: Число для отображения
        :return: Строковое представление числа
        """
        value = float(value)
        fraction = Fraction(value).limit_denominator(10000)

        if isclose(value, float(fraction), rel_tol=1e-10, abs_tol=1e-12):
            return str(fraction)

        return f"{value:.8g}"

    def print_steps(self, history: Iterable["TableSnapshot"]):
        """Выводит историю таблиц с заголовками фаз

        :param history: Последовательность снимков таблиц
        :return: None
        """
        current_phase = None

        for index, step in enumerate(history, start=1):
            if step.phase != current_phase:
                title = "Вспомогательная задача" if step.phase == "I" else "Основная задача"
                self.console.print()
                self.console.print(Text(f"Фаза {step.phase}. {title}", style="bold cyan"))
                current_phase = step.phase

            self.console.print()
            self.console.print(Text(f"{index:02d}. {step.action}", style="bold"))

            table = Table(
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="dim",
                padding=(0, 1),
                expand=False,
            )

            table.add_column("Базис", justify="left", no_wrap=True)
            for name in step.nonbasis:
                table.add_column(name, justify="right", no_wrap=True)
            table.add_column("b / −Q", justify="right", no_wrap=True, style="bold")

            for name, values in zip(step.basis, step.values[:-1]):
                table.add_row(name, *(self.format_number(v) for v in values))

            if step.basis:
                table.add_section()
            table.add_row(
                "Цель", *(self.format_number(v) for v in step.values[-1]), style="bold cyan"
            )

            self.console.print(table)
