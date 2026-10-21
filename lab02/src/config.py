from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    """Настройки, прочитанные из .env без изменения окружения процесса."""

    expression: str
    a: float
    b: float
    eps: float
    estimation_intervals: int
    max_iterations: int

    @classmethod
    def read(cls, path: Path) -> "Settings":
        if not path.is_file():
            raise ValueError(f"Нет {path}. Скопируйте lab02/.env.example в lab02/.env.")
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
        keys = ("FUNCTION", "A", "B", "EPS", "ESTIMATION_INTERVALS", "MAX_ITERATIONS")
        missing = [key for key in keys if not values.get(key)]
        if missing:
            raise ValueError("Не заданы параметры: " + ", ".join(missing))
        try:
            result = cls(values["FUNCTION"], float(values["A"]), float(values["B"]),
                         float(values["EPS"]), int(values["ESTIMATION_INTERVALS"]),
                         int(values["MAX_ITERATIONS"]))
        except (TypeError, ValueError) as error:
            raise ValueError("Проверьте числовые параметры .env; десятичный разделитель — точка.") from error
        if not all(isfinite(x) for x in (result.a, result.b, result.eps, result.b-result.a)):
            raise ValueError("Границы, длина отрезка и EPS должны быть конечными.")
        if result.a >= result.b or result.eps <= 0:
            raise ValueError("Требуется A < B и EPS > 0.")
        if result.estimation_intervals < 2 or result.max_iterations < 1:
            raise ValueError("ESTIMATION_INTERVALS >= 2, MAX_ITERATIONS >= 1.")
        return result

