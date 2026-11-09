import copy
import sys
import unittest
from pathlib import Path

# Allow direct execution to import modules from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.binding import bind_resources
from hls.dag import build_dag
from hls.parser import parse_line
from hls.scheduler import schedule_dag
from hls.ssa import convert_to_ssa


def graph(*lines):
    # Build a DAG from equation strings for binding tests.
    return build_dag(convert_to_ssa([
        parse_line(line, index) for index, line in enumerate(lines, 1)
    ]))


class TestBinding(unittest.TestCase):
    def test_shared_units(self):
        # Operations in separate cycles reuse the same adder.
        dag = graph("X=A+B", "Y=X+C", "Z=X-D")
        schedule = schedule_dag(dag)
        original = copy.deepcopy((dag, schedule))
        result = bind_resources(dag, schedule)
        self.assertEqual(result["binding"], {
            "X_1": "adder_0", "Y_1": "adder_0", "Z_1": "subtractor_0"})
        self.assertEqual(result["resource_counts"], {"+": 1, "-": 1, "*": 0})
        self.assertEqual(result["units"]["adder_0"]["operations"], ["X_1", "Y_1"])
        self.assertEqual((dag, schedule), original)

    def test_parallel_units_and_resource_failure(self):
        # Simultaneous additions need separate units or a different schedule.
        dag = graph("X=A+B", "Y=C+D")
        schedule = schedule_dag(dag)
        self.assertEqual(bind_resources(dag, schedule)["resource_counts"]["+"], 2)
        with self.assertRaises(ValueError):
            bind_resources(dag, schedule, {"+": 1})
        constrained = schedule_dag(dag, "constrained_asap", {"+": 1})
        self.assertEqual(bind_resources(dag, constrained, {"+": 1})["resource_counts"]["+"], 1)

    def test_multicycle_occupancy(self):
        # A unit stays occupied until its full latency elapses.
        dag = graph("X=A*B", "Y=C*D", "Z=E*F")
        result = bind_resources(dag, {"X_1": 0, "Y_1": 1, "Z_1": 3},
                                latencies={"*": 3})
        self.assertEqual(result["resource_counts"]["*"], 2)
        self.assertEqual(result["binding"]["X_1"], result["binding"]["Z_1"])

    def test_invalid_schedule(self):
        # Reject missing operations, invalid starts, and premature consumers.
        dag = graph("X=A+B", "Y=X*C")
        for schedule in ({"X_1": 0}, {"X_1": 0, "Y_1": 0},
                         {"X_1": -1, "Y_1": 1}, {"X_1": True, "Y_1": 1}):
            with self.subTest(schedule=schedule), self.assertRaises(ValueError):
                bind_resources(dag, schedule)

    def test_invalid_configuration(self):
        # Reject invalid unit counts and latency definitions.
        dag = graph("X=A+B")
        for count in (0, -1, True, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                bind_resources(dag, {"X_1": 0}, {"+": count})
        with self.assertRaises(ValueError):
            bind_resources(dag, {"X_1": 0}, latencies={"*": 1})

    def test_empty(self):
        # Empty graphs allocate no hardware.
        self.assertEqual(bind_resources({}, {}), {
            "binding": {}, "units": {}, "resource_counts": {"+": 0, "-": 0, "*": 0}})


if __name__ == "__main__":
    unittest.main()
