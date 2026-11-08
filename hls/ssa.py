"""
EC551 HLS Synthesizer
Static Single Assignment (SSA) Conversion
"""

import argparse
from pathlib import Path

try:
    from .parser import parse_file
except ImportError:
    from parser import parse_file


def convert_to_ssa(equations: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Convert parsed equations into SSA form.

    Each assignment receives a unique variable version.
    Operands reference the latest assigned version.

    Variables that have not been assigned are treated as
    primary inputs and retain their original names.
    """

    versions = {}
    ssa_equations = []

    for equation in equations:

        result = equation["result"]
        operand1 = equation["operand1"]
        operand2 = equation["operand2"]
        operator = equation["operator"]

        # Resolve operand versions before updating the result.
        # This handles cases such as X = X + A.

        if operand1 in versions:
            operand1_ssa = f"{operand1}_{versions[operand1]}"
        else:
            operand1_ssa = operand1

        if operand2 in versions:
            operand2_ssa = f"{operand2}_{versions[operand2]}"
        else:
            operand2_ssa = operand2

        # Create a new version for the result variable.

        versions[result] = versions.get(result, 0) + 1

        result_ssa = f"{result}_{versions[result]}"

        # Store the SSA equation using the same structure
        # produced by parser.py.

        ssa_equations.append({
            "result": result_ssa,
            "operand1": operand1_ssa,
            "operator": operator,
            "operand2": operand2_ssa
        })

    return ssa_equations


def format_ssa(equations: list[dict[str, str]]) -> str:
    """
    Convert SSA equations into readable text.
    """

    lines = []

    for equation in equations:

        result = equation["result"]
        operand1 = equation["operand1"]
        operand2 = equation["operand2"]
        operator = equation["operator"]

        line = f"{result}={operand1}{operator}{operand2}"

        lines.append(line)

    return "\n".join(lines)


def export_ssa(equations: list[dict[str, str]], output_path: str | Path):
    """
    Export SSA equations to a text file.
    """

    output_path = Path(output_path)

    output_path.write_text(
        format_ssa(equations) + "\n",
        encoding="utf-8"
    )


def main():

    cli = argparse.ArgumentParser(
        description="Convert EC551 equations to SSA form."
    )

    cli.add_argument(
        "input_file",
        help="Path to input equations text file"
    )

    cli.add_argument(
        "--export-ssa",
        nargs="?",
        const="ssa_output.txt",
        metavar="OUTPUT_FILE",
        help="Export SSA equations to a text file"
    )

    args = cli.parse_args()

    # Step 1: Parse the input equations.
    equations = parse_file(args.input_file)

    # Step 2: Convert equations into SSA form.
    ssa_equations = convert_to_ssa(equations)

    # Step 3: Display the SSA equations.
    print(format_ssa(ssa_equations))

    # Step 4: Export SSA if requested.
    if args.export_ssa is not None:

        export_ssa(ssa_equations, args.export_ssa)

        print(f"SSA exported to {args.export_ssa}")


if __name__ == "__main__":
    main()