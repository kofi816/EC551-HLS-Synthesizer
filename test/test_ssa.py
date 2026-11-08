"""
Unit tests for EC551 HLS Static Single Assignment (SSA) conversion.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.parser import parse_line
from hls.ssa import convert_to_ssa, export_ssa, format_ssa


def parsed(*lines):
    """Parse equations before SSA conversion."""
    return [
        parse_line(line, index)
        for index, line in enumerate(lines, start=1)
    ]


class TestSSA(unittest.TestCase):

    def test_assignment_example(self):
        """Test the equations provided in the assignment."""

        equations = parsed(
            "X=A+B",
            "Y=X+A",
            "Z=X-B",
            "Q=B*Z"
        )

        actual = format_ssa(convert_to_ssa(equations))

        expected = (
            "X_1=A+B\n"
            "Y_1=X_1+A\n"
            "Z_1=X_1-B\n"
            "Q_1=B*Z_1"
        )

        self.assertEqual(actual, expected)

    def test_repeated_assignments(self):
        """Test multiple assignments to the same variable."""

        equations = parsed(
            "X=A+B",
            "X=X+C",
            "Y=X*D",
            "X=Y-A",
            "Z=X+B"
        )

        actual = format_ssa(convert_to_ssa(equations))

        expected = (
            "X_1=A+B\n"
            "X_2=X_1+C\n"
            "Y_1=X_2*D\n"
            "X_3=Y_1-A\n"
            "Z_1=X_3+B"
        )

        self.assertEqual(actual, expected)

    def test_primary_inputs_remain_unversioned(self):
        """Variables without prior assignments remain primary inputs."""

        actual = convert_to_ssa(parsed("X=A+B"))

        self.assertEqual(actual[0]["operand1"], "A")
        self.assertEqual(actual[0]["operand2"], "B")

    def test_reads_resolved_before_write(self):
        """Verify operands use previous versions before reassignment."""

        equations = parsed(
            "X=X+A",
            "X=X+X"
        )

        actual = format_ssa(convert_to_ssa(equations))

        expected = (
            "X_1=X+A\n"
            "X_2=X_1+X_1"
        )

        self.assertEqual(actual, expected)

    def test_independent_version_counters(self):
        """Each variable maintains its own version counter."""

        equations = parsed(
            "X=A+B",
            "Y=C+D",
            "X=X+Y",
            "Y=X-Y"
        )

        actual = format_ssa(convert_to_ssa(equations))

        expected = (
            "X_1=A+B\n"
            "Y_1=C+D\n"
            "X_2=X_1+Y_1\n"
            "Y_2=X_2-Y_1"
        )

        self.assertEqual(actual, expected)

    def test_empty_input(self):
        """Test SSA conversion with no equations."""

        self.assertEqual(convert_to_ssa([]), [])
        self.assertEqual(format_ssa([]), "")

    def test_output_structure(self):
        """Verify SSA preserves the parser's dictionary format."""

        actual = convert_to_ssa(parsed("X=A*B"))

        expected = [{
            "result": "X_1",
            "operand1": "A",
            "operator": "*",
            "operand2": "B"
        }]

        self.assertEqual(actual, expected)

    def test_does_not_modify_parsed_input(self):
        """Verify SSA conversion does not modify the original equations."""

        equations = parsed(
            "X=A+B",
            "X=X-C"
        )

        original = [equation.copy() for equation in equations]

        convert_to_ssa(equations)

        self.assertEqual(equations, original)

    def test_export_ssa(self):
        """Verify SSA equations are correctly exported to a text file."""

        equations = convert_to_ssa(
            parsed(
                "X=A+B",
                "Y=X*A"
            )
        )

        with TemporaryDirectory() as directory:

            output = Path(directory) / "ssa.txt"

            export_ssa(equations, output)

            actual = output.read_text(encoding="utf-8")

            expected = (
                "X_1=A+B\n"
                "Y_1=X_1*A\n"
            )

            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()