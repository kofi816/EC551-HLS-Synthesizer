"""Parse EC551 HLS arithmetic equations from a text file."""

import re
from pathlib import Path

MAX_EQUATIONS = 20

IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"

EQUATION_PATTERN = re.compile(
    rf"^\s*({IDENTIFIER})\s*=\s*({IDENTIFIER})\s*([+*\-])\s*({IDENTIFIER})\s*$"
)


def parse_line(line: str, line_number: int) -> dict[str, str]:
    """Parse one equation into result, operand1, operator, and operand2."""

    match = EQUATION_PATTERN.fullmatch(line)

    if match is None:
        raise ValueError(
            f"Line {line_number}: invalid equation {line.strip()!r}. "
            "Expected RESULT = OPERAND1 (+, -, or *) OPERAND2."
        )

    result, operand1, operator, operand2 = match.groups()

    return {
        "result": result,
        "operand1": operand1,
        "operator": operator,
        "operand2": operand2,
    }


def parse_file(file_path: str | Path) -> list[dict[str, str]]:
    """Read and parse up to 20 nonempty equation lines from a text file."""

    path = Path(file_path)
    equations = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            if not line.strip():
                continue

            if len(equations) >= MAX_EQUATIONS:
                raise ValueError(
                    f"Maximum of {MAX_EQUATIONS} equations exceeded "
                    f"(line {line_number})."
                )

            equations.append(parse_line(line, line_number))

    if not equations:
        raise ValueError("Input file contains no equations.")

    return equations


if __name__ == "__main__":
    import argparse

    cli = argparse.ArgumentParser(
        description="Parse arithmetic equations for EC551 HLS."
    )

    cli.add_argument(
        "input_file",
        help="Path to the equation text file"
    )

    args = cli.parse_args()

    for equation in parse_file(args.input_file):
        print(equation)