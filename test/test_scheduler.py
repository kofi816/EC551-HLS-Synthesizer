"""Verify scheduling dependencies, resource occupancy, and deadlines."""
import copy
import sys
import unittest
from pathlib import Path

# Allow direct execution to import modules from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.dag import build_dag
from hls.parser import parse_line
from hls.ssa import convert_to_ssa
from hls.scheduler import schedule_dag


def graph(*lines):
    return build_dag(convert_to_ssa([
        parse_line(line, i) for i, line in enumerate(lines, 1)
    ]))


class TestScheduler(unittest.TestCase):
    def test_modes_obey_dependencies_and_resources(self):
        dag = graph("X=A+B", "Y=C+D", "P=E*F", "Z=X*Y", "Q=Z+P")
        original = copy.deepcopy(dag)
        latencies = {"+": 2, "-": 1, "*": 3}
        for mode in ("asap", "constrained_asap", "alap", "constrained_alap", "custom"):
            with self.subTest(mode=mode):
                result = schedule_dag(dag, mode, {"+": 1, "*": 1}, 20, latencies)
                self.assertEqual(set(result), set(dag))
                for name, node in dag.items():
                    self.assertGreaterEqual(result[name], 0)
                    for dep in node["dependencies"]:
                        self.assertGreaterEqual(result[name], result[dep] + latencies[dag[dep]["operator"]])
                finish = max(result[n] + latencies[dag[n]["operator"]] for n in dag)
                if mode in ("alap", "constrained_alap"):
                    self.assertEqual(finish, 20)
                if mode in ("constrained_asap", "constrained_alap", "custom"):
                    for cycle in range(finish):
                        for operator in ("+", "*"):
                            active = [n for n in dag if dag[n]["operator"] == operator
                                      and result[n] <= cycle < result[n] + latencies[operator]]
                            self.assertLessEqual(len(active), 1)
        self.assertEqual(dag, original)

    def test_exact_forward_and_backward(self):
        dag = graph("X=A+B", "Y=C+D", "Z=X*Y")
        self.assertEqual(schedule_dag(dag, "constrained_asap", {"+": 1}),
                         {"X_1": 0, "Y_1": 1, "Z_1": 2})
        self.assertEqual(schedule_dag(dag, "alap", latency_bound=5),
                         {"X_1": 3, "Y_1": 3, "Z_1": 4})

    def test_custom_prioritizes_critical_path(self):
        dag = graph("X=A+B", "Y=C+D", "Z=Y*E", "Q=Z-F")
        result = schedule_dag(dag, "custom", {"+": 1})
        self.assertEqual(result["Y_1"], 0)
        self.assertEqual(result["X_1"], 1)

    def test_invalid_inputs(self):
        dag = graph("X=A+B", "Y=X*C")
        for kwargs in ({"mode": "alap", "latency_bound": 1},
                       {"mode": "constrained_asap", "resources": {"+": 0}},
                       {"mode": "custom", "latencies": {"+": True, "*": 1}},
                       {"mode": "missing"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                schedule_dag(dag, **kwargs)
        broken = {"X": {"operator": "+", "dependencies": ["X"]}}
        with self.assertRaises(ValueError):
            schedule_dag(broken, "custom")
        broken["X"]["dependencies"] = ["missing"]
        with self.assertRaises(ValueError):
            schedule_dag(broken, "constrained_alap")

    def test_empty(self):
        for mode in ("asap", "constrained_asap", "alap", "constrained_alap", "custom"):
            self.assertEqual(schedule_dag({}, mode), {})


if __name__ == "__main__":
    unittest.main()
