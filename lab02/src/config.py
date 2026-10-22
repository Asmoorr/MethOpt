from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    """Строковые настройки .env после преобразования в числовые типы

    :param expression: Математическое выражение от x
    :param a: Левая граница
    :param b: Правая граница
    :param eps: Точность по значению функции
    :param estimation_intervals: Число интервалов начальной сетки
    :param max_iterations: Лимит новых точек поиска
    """

    expression: str
    a: float
    b: float
    eps: float
    estimation_intervals: int
    max_iterations: int

    @classmethod
    def read(cls, path: Path) -> "Settings":
        """Читает обязательные параметры и проверяет их значения

        :param path: Путь к локальному файлу .env
        :return: Проверенные настройки запуска
        """
        if not path.is_file():
            raise ValueError(f"Нет {path}. Скопируйте lab02/.env.example в lab02/.env.")
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
        keys = ("FUNCTION", "A", "B", "EPS", "ESTIMATION_INTERVALS", "MAX_ITERATIONS")
        missing = [key for key in keys if not values.get(key)]
        if missing:
            raise ValueError("Не заданы параметры: " + ", ".join(missing))
        try:
            result = cls(
                expression=values["FUNCTION"],
                a=float(values["A"]),
                b=float(values["B"]),
                eps=float(values["EPS"]),
                estimation_intervals=int(values["ESTIMATION_INTERVALS"]),
                max_iterations=int(values["MAX_ITERATIONS"]),
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Проверьте числовые параметры .env; десятичный разделитель — точка.") from error
        if not all(isfinite(x) for x in (result.a, result.b, result.eps, result.b - result.a)):
            raise ValueError("Границы, длина отрезка и EPS должны быть конечными.")
        if result.a >= result.b or result.eps <= 0:
            raise ValueError("Требуется A < B и EPS > 0.")
        if result.estimation_intervals < 2 or result.max_iterations < 1:
            raise ValueError("ESTIMATION_INTERVALS >= 2, MAX_ITERATIONS >= 1.")
        return result

