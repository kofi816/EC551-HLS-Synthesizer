"""
EC551 HLS Synthesizer
Unit Tests for Unconstrained ASAP Scheduling
"""

import sys
import unittest
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.parser import parse_line
from hls.ssa import convert_to_ssa
from hls.dag import build_dag
from hls.scheduling.asap import asap_schedule


def schedule_equations(*lines, latencies=None):
    """
    Run the complete frontend pipeline:
    Parser -> SSA -> DAG -> ASAP
    """

    equations = [
        parse_line(line, number)
        for number, line in enumerate(lines, 1)
    ]

    ssa_equations = convert_to_ssa(equations)
    dag = build_dag(ssa_equations)

    return asap_schedule(dag, latencies)


class TestASAP(unittest.TestCase):

    def test_assignment_example(self):
        """Verify ASAP scheduling for the assignment example."""

        schedule = schedule_equations(
            "X=A+B",
            "Y=X+A",
            "Z=X-B",
            "Q=B*Z"
        )

        expected = {
            "X_1": 0,
            "Y_1": 1,
            "Z_1": 1,
            "Q_1": 2
        }

        self.assertEqual(schedule, expected)

    def test_independent_operations(self):
        """Independent operations should execute in parallel."""

        schedule = schedule_equations(
            "X=A+B",
            "Y=C-D",
            "Z=E*F"
        )

        expected = {
            "X_1": 0,
            "Y_1": 0,
            "Z_1": 0
        }

        self.assertEqual(schedule, expected)

    def test_dependency_chain(self):
        """Verify sequential execution of dependent operations."""

        schedule = schedule_equations(
            "X=A+B",
            "Y=X*C",
            "Z=Y-D",
            "Q=Z+E"
        )

        expected = {
            "X_1": 0,
            "Y_1": 1,
            "Z_1": 2,
            "Q_1": 3
        }

        self.assertEqual(schedule, expected)

    def test_multiple_dependencies(self):
        """An operation must wait for all preceding operations."""

        schedule = schedule_equations(
            "X=A+B",
            "Y=C-D",
            "Z=X*Y"
        )

        expected = {
            "X_1": 0,
            "Y_1": 0,
            "Z_1": 1
        }

        self.assertEqual(schedule, expected)

    def test_custom_latencies(self):
        """Verify scheduling with different operation latencies."""

        latencies = {
            "+": 1,
            "-": 2,
            "*": 3
        }

        schedule = schedule_equations(
            "X=A*B",
            "Y=X+C",
            "Z=Y-D",
            latencies=latencies
        )

        expected = {
            "X_1": 0,
            "Y_1": 3,
            "Z_1": 4
        }

        self.assertEqual(schedule, expected)

    def test_wait_for_slowest_predecessor(self):
        """Verify scheduling waits for the latest dependency."""

        latencies = {
            "+": 1,
            "-": 1,
            "*": 3
        }

        schedule = schedule_equations(
            "X=A+B",
            "Y=C*D",
            "Z=X+Y",
            latencies=latencies
        )

        expected = {
            "X_1": 0,
            "Y_1": 0,
            "Z_1": 3
        }

        self.assertEqual(schedule, expected)

    def test_variable_reassignment(self):
        """Verify correct scheduling after SSA reassignment."""

        schedule = schedule_equations(
            "X=A+B",
            "X=X+C",
            "Y=X*D"
        )

        expected = {
            "X_1": 0,
            "X_2": 1,
            "Y_1": 2
        }

        self.assertEqual(schedule, expected)

    def test_empty_dag(self):
        """An empty DAG should produce an empty schedule."""

        self.assertEqual(asap_schedule({}), {})

    def test_invalid_latency(self):
        """Reject invalid operation latencies."""

        dag = build_dag(
            convert_to_ssa([
                parse_line("X=A+B", 1)
            ])
        )

        for invalid in (0, -1, 1.5, True):

            with self.subTest(latency=invalid):

                with self.assertRaises(ValueError):

                    asap_schedule(
                        dag,
                        {
                            "+": invalid,
                            "-": 1,
                            "*": 1
                        }
                    )

    def test_missing_latency(self):
        """Reject missing operation latency definitions."""

        dag = build_dag(
            convert_to_ssa([
                parse_line("X=A*B", 1)
            ])
        )

        with self.assertRaises(ValueError):

            asap_schedule(
                dag,
                {
                    "+": 1,
                    "-": 1
                }
            )

    def test_unknown_dependency(self):
        """Reject dependencies referencing nonexistent operations."""

        dag = {
            "X_1": {
                "operator": "+",
                "operands": ["A", "B"],
                "dependencies": ["MISSING"]
            }
        }

        with self.assertRaises(ValueError):
            asap_schedule(dag)

    def test_cycle_detection(self):
        """Reject cyclic dependencies."""

        dag = {
            "X_1": {
                "operator": "+",
                "operands": ["Y_1", "A"],
                "dependencies": ["Y_1"]
            },
            "Y_1": {
                "operator": "*",
                "operands": ["X_1", "B"],
                "dependencies": ["X_1"]
            }
        }

        with self.assertRaises(ValueError):
            asap_schedule(dag)

    def test_dag_not_modified(self):
        """Scheduling must not modify the original DAG."""

        dag = build_dag(
            convert_to_ssa([
                parse_line("X=A+B", 1),
                parse_line("Y=X*C", 2)
            ])
        )

        import copy

        original = copy.deepcopy(dag)

        asap_schedule(dag)

        self.assertEqual(dag, original)


if __name__ == "__main__":
    unittest.main()