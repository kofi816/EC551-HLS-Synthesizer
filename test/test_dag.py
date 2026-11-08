"""
Unit tests for the EC551 HLS DAG builder.
"""

import sys
import unittest
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.parser import parse_line
from hls.ssa import convert_to_ssa
from hls.dag import build_dag, get_primary_inputs


def make_dag(*lines):
    """
    Build a DAG using the complete frontend pipeline:
    Parser -> SSA -> DAG
    """

    parsed = [
        parse_line(line, number)
        for number, line in enumerate(lines, 1)
    ]

    ssa_equations = convert_to_ssa(parsed)

    return build_dag(ssa_equations)


class TestDAG(unittest.TestCase):

    def test_assignment_example(self):
        """Test the assignment's example equations."""

        dag = make_dag(
            "X=A+B",
            "Y=X+A",
            "Z=X-B",
            "Q=B*Z"
        )

        expected = {
            "X_1": {
                "operator": "+",
                "operands": ["A", "B"],
                "dependencies": []
            },
            "Y_1": {
                "operator": "+",
                "operands": ["X_1", "A"],
                "dependencies": ["X_1"]
            },
            "Z_1": {
                "operator": "-",
                "operands": ["X_1", "B"],
                "dependencies": ["X_1"]
            },
            "Q_1": {
                "operator": "*",
                "operands": ["B", "Z_1"],
                "dependencies": ["Z_1"]
            }
        }

        self.assertEqual(dag, expected)

    def test_primary_inputs(self):
        """Verify primary inputs are correctly identified."""

        dag = make_dag(
            "X=A+B",
            "Y=X+A",
            "Z=X-B",
            "Q=B*Z"
        )

        self.assertEqual(
            get_primary_inputs(dag),
            ["A", "B"]
        )

    def test_independent_operations(self):
        """Verify independent operations have no dependencies."""

        dag = make_dag(
            "X=A+B",
            "Y=C*D"
        )

        self.assertEqual(dag["X_1"]["dependencies"], [])
        self.assertEqual(dag["Y_1"]["dependencies"], [])

        self.assertEqual(
            get_primary_inputs(dag),
            ["A", "B", "C", "D"]
        )

    def test_multiple_dependencies(self):
        """Verify operations can depend on multiple preceding results."""

        dag = make_dag(
            "X=A+B",
            "Y=C-D",
            "Z=X*Y"
        )

        self.assertEqual(
            dag["Z_1"]["dependencies"],
            ["X_1", "Y_1"]
        )

    def test_duplicate_operand_dependency_is_unique(self):
        """Verify repeated operands produce only one dependency edge."""

        dag = make_dag(
            "X=A+B",
            "Y=X*X"
        )

        self.assertEqual(
            dag["Y_1"]["operands"],
            ["X_1", "X_1"]
        )

        self.assertEqual(
            dag["Y_1"]["dependencies"],
            ["X_1"]
        )

    def test_reassignment_uses_latest_version(self):
        """Verify dependencies reference the latest SSA version."""

        dag = make_dag(
            "X=A+B",
            "X=X+C",
            "Y=X*D"
        )

        self.assertEqual(
            dag["X_2"]["dependencies"],
            ["X_1"]
        )

        self.assertEqual(
            dag["Y_1"]["dependencies"],
            ["X_2"]
        )

        self.assertEqual(
            get_primary_inputs(dag),
            ["A", "B", "C", "D"]
        )

    def test_read_before_assignment_is_primary_input(self):
        """Verify variables read before assignment are primary inputs."""

        dag = make_dag(
            "Y=X+A",
            "X=B+C"
        )

        self.assertEqual(
            dag["Y_1"]["dependencies"],
            []
        )

        self.assertIn("X", get_primary_inputs(dag))

        self.assertNotIn(
            "X_1",
            dag["Y_1"]["dependencies"]
        )

    def test_empty_dag(self):
        """Verify empty input produces an empty DAG."""

        self.assertEqual(build_dag([]), {})
        self.assertEqual(get_primary_inputs({}), [])

    def test_duplicate_results_rejected(self):
        """Verify duplicate SSA result names are rejected."""

        equations = [
            {
                "result": "X_1",
                "operand1": "A",
                "operator": "+",
                "operand2": "B"
            },
            {
                "result": "X_1",
                "operand1": "C",
                "operator": "-",
                "operand2": "D"
            }
        ]

        with self.assertRaisesRegex(ValueError, "must be unique"):
            build_dag(equations)

    def test_forward_dependency_rejected(self):
        """Verify forward references to computed results are rejected."""

        equations = [
            {
                "result": "Y_1",
                "operand1": "X_1",
                "operator": "+",
                "operand2": "A"
            },
            {
                "result": "X_1",
                "operand1": "B",
                "operator": "*",
                "operand2": "C"
            }
        ]

        with self.assertRaisesRegex(
            ValueError,
            "before it is computed"
        ):
            build_dag(equations)

    def test_self_dependency_rejected(self):
        """Verify an operation cannot depend on itself."""

        equations = [
            {
                "result": "X_1",
                "operand1": "X_1",
                "operator": "+",
                "operand2": "A"
            }
        ]

        with self.assertRaisesRegex(
            ValueError,
            "before it is computed"
        ):
            build_dag(equations)


if __name__ == "__main__":
    unittest.main()