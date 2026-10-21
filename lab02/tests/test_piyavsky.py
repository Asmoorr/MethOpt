import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Settings
from expression import Expression
from models import Point
from piyavsky import PiyavskySolver, intersection


class MethodTests(unittest.TestCase):
    def test_excel_first_intersection(self):
        f = Expression("0.5*x+0.2*cos(3.14*x)+0.2*sin(6.28*x)")
        p = intersection(Point(-2, f(-2)), Point(1, f(1)), 2.154299741229259)
        self.assertAlmostEqual(p.x, -0.7548600996983552, places=12)
        self.assertAlmostEqual(p.y, f(-2)-2.154299741229259*(p.x+2), places=12)

    def test_rastrigin_and_previous_minorant(self):
        f = Expression("x**2+10*(1-cos(2*pi*x))")
        result = PiyavskySolver().solve(f, -2, 2, 0.01)
        self.assertEqual(result.status, "converged")
        self.assertLessEqual(abs(result.point.y), 0.01)
        self.assertLess(result.history[-1].gap, 0.01)
        self.assertEqual(result.estimation_evaluations, 10001)
        self.assertEqual(result.search_evaluations, len(result.history))
        points = [Point(-2, f(-2)), Point(2, f(2))]
        for step in result.history:
            lower = min(intersection(l, r, result.lipschitz).y
                        for l, r in zip(points, points[1:]))
            self.assertAlmostEqual(lower, step.lower, places=10)
            self.assertAlmostEqual(step.gap, step.point.y-lower, places=10)
            points.append(step.point)
            points.sort(key=lambda p: p.x)

    def test_boundary_and_constant(self):
        for f, expected in [(lambda x: x, -2), (lambda x: 7, 7)]:
            with self.subTest(expected=expected):
                result = PiyavskySolver().solve(f, -2, 2, 0.01)
                self.assertEqual(result.status, "converged")
                self.assertAlmostEqual(result.point.y, expected)

    def test_off_center_minimum(self):
        result = PiyavskySolver().solve(lambda x: (x-0.37)**2, -1, 2, 1e-4)
        self.assertEqual(result.status, "converged")
        self.assertLessEqual(result.point.y, 1e-4)

    def test_limit(self):
        result = PiyavskySolver().solve(lambda x: x*x, -1, 1, 1e-12, max_iterations=1)
        self.assertEqual(result.status, "iteration-limit")

    def test_underestimated_l_is_not_updated(self):
        result = PiyavskySolver().solve(lambda x: math.sin(2*math.pi*x), 0, 1,
                                       0.01, estimation_intervals=2)
        self.assertEqual(result.status, "invalid-lipschitz")

    def test_bad_expression(self):
        for source in ("__import__('os')", "x.__class__", "[x]", "sin(x, x)"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                Expression(source)
        with self.assertRaises(ValueError):
            Expression("sqrt(x)")(-1)

    def test_env(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('FUNCTION="x + sin(pi*x)"\nA=-1\nB=1\nEPS=0.01\n'
                            'ESTIMATION_INTERVALS=100\nMAX_ITERATIONS=200\n', encoding="utf-8")
            settings = Settings.read(path)
            self.assertEqual(settings.expression, "x + sin(pi*x)")
            self.assertEqual(settings.max_iterations, 200)
            path.write_text("FUNCTION=x", encoding="utf-8")
            with self.assertRaises(ValueError):
                Settings.read(path)


if __name__ == "__main__":
    unittest.main()

