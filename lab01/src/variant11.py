import numpy as np
from scipy.optimize import linprog

from console_tables import ConsoleTablePrinter
from models import LinearProgram
from simplex import TwoPhaseSimplex


problem = LinearProgram(
    c=np.array([1, 2, 4, 1], dtype=float),
    A=np.array([[1, 1, 1, 0], [0, 1, 2, 1], [1, 0, 0, 1]], dtype=float),
    b=np.array([10, 6, 2], dtype=float),
    signs=["<=", "=", ">="],
    sense="max",
)

solver = TwoPhaseSimplex(pivot_rule="most-negative")
solution = solver.solve(problem)

print("s - дополнительная переменная, a - искусственная; Цель: коэффициенты и -Q.")
ConsoleTablePrinter().print_steps(solver.history)

print(f"\nСтатус: {solution.status}. Итераций: {solution.iterations}")
if solution.status == "optimal" and solution.x is not None and solution.value is not None:
    print("x* =", np.round(solution.x, 8))
    print(f"Целевая функция = {solution.value:.8g}")

reference = linprog(
    -problem.c,
    A_ub=[problem.A[0], -problem.A[2]],
    b_ub=[problem.b[0], -problem.b[2]],
    A_eq=[problem.A[1]],
    b_eq=[problem.b[1]],
    bounds=problem.bounds,
    method="highs",
)

if (
    reference.success
    and solution.status == "optimal"
    and solution.x is not None
    and solution.value is not None
):
    lhs = problem.A @ solution.x
    feasible = (
        lhs[0] <= problem.b[0] + 1e-7
        and np.isclose(lhs[1], problem.b[1], atol=1e-7, rtol=0)
        and lhs[2] >= problem.b[2] - 1e-7
        and np.all(solution.x >= -1e-7)
    )
    matches = feasible and np.isclose(solution.value, -reference.fun)

    print("\nSciPy x* =", np.round(reference.x, 8))
    print(f"SciPy: целевая функция = {-reference.fun:.8g}")
    print("Проверка SciPy:", "совпадает" if matches else "НЕ совпадает")
else:
    print("\nПроверка SciPy: оптимальное решение не получено.")
    print(reference.message)
