"""
Unit tests for the EC551 HLS equation parser.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow running this file directly from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.parser import parse_file, parse_line


class TestParseLine(unittest.TestCase):

    def test_supported_operators(self):
        """Test addition, subtraction, and multiplication."""

        for operator in ("+", "-", "*"):
            with self.subTest(operator=operator):
                self.assertEqual(
                    parse_line(f"X=A{operator}B", 1),
                    {
                        "result": "X",
                        "operand1": "A",
                        "operator": operator,
                        "operand2": "B"
                    }
                )

    def test_whitespace(self):
        """Test equations containing whitespace."""

        self.assertEqual(
            parse_line("  output_1 = input2 * _temp  ", 3),
            {
                "result": "output_1",
                "operand1": "input2",
                "operator": "*",
                "operand2": "_temp"
            }
        )

    def test_reassignment_is_preserved(self):
        """Verify reassigned variables remain unchanged during parsing."""

        result = parse_line("X=X+A", 2)

        self.assertEqual(result["result"], "X")
        self.assertEqual(result["operand1"], "X")

    def test_invalid_equations(self):
        """Test rejection of malformed equations."""

        invalid_equations = (
            "X=A",
            "X=A/B",
            "X=A+",
            "=A+B",
            "X=A+B+C",
            "1X=A+B",
            "X=A+5"
        )

        for equation in invalid_equations:
            with self.subTest(equation=equation):
                with self.assertRaisesRegex(ValueError, "Line 7"):
                    parse_line(equation, 7)


class TestParseFile(unittest.TestCase):

    def parse_text(self, text):
        """Create a temporary input file and parse its contents."""

        with TemporaryDirectory() as directory:

            path = Path(directory) / "equations.txt"

            path.write_text(text, encoding="utf-8")

            return parse_file(path)

    def test_example_input(self):
        """Test the example equations from the assignment."""

        equations = self.parse_text(
            "X=A+B\n"
            "Y=X+A\n"
            "Z=X-B\n"
            "Q=B*Z\n"
        )

        self.assertEqual(len(equations), 4)

        self.assertEqual(equations[0]["result"], "X")
        self.assertEqual(equations[1]["operand1"], "X")
        self.assertEqual(equations[2]["operator"], "-")
        self.assertEqual(equations[3]["operand2"], "Z")

    def test_blank_lines_are_ignored(self):
        """Verify empty lines do not count as equations."""

        equations = self.parse_text(
            "\n"
            "X=A+B\n"
            "  \n"
            "Y=X+A\n"
        )

        self.assertEqual(len(equations), 2)

    def test_twenty_equations_allowed(self):
        """Verify exactly 20 equations are accepted."""

        equations = self.parse_text("X=A+B\n" * 20)

        self.assertEqual(len(equations), 20)

    def test_more_than_twenty_equations_rejected(self):
        """Verify more than 20 equations are rejected."""

        with self.assertRaisesRegex(
            ValueError,
            "Maximum of 20 equations exceeded"
        ):
            self.parse_text("X=A+B\n" * 21)

    def test_empty_file_rejected(self):
        """Verify an empty input file raises an error."""

        with self.assertRaisesRegex(ValueError, "no equations"):
            self.parse_text(" \n\n")

    def test_error_reports_physical_line_number(self):
        """Verify error messages identify the correct input line."""

        with self.assertRaisesRegex(ValueError, "Line 3"):
            self.parse_text(
                "X=A+B\n"
                "\n"
                "Y=A/B\n"
            )

    def test_missing_file(self):
        """Verify a missing input file raises FileNotFoundError."""

        with TemporaryDirectory() as directory:

            missing_path = Path(directory) / "missing.txt"

            with self.assertRaises(FileNotFoundError):
                parse_file(missing_path)


if __name__ == "__main__":
    unittest.main()