"""EC551 HLS Synthesizer - Main Entry Point."""

import argparse
import json
from pathlib import Path

from hls.parser import parse_file
from hls.ssa import convert_to_ssa
from hls.dag import build_dag
from hls.scheduling.asap import asap_schedule


def run_frontend(input_path: str) -> dict:
    """
    Run the HLS frontend pipeline.

    Input equations -> Parser -> SSA -> DAG -> ASAP Scheduling
    """

    # Step 1: Parse equations
    equations = parse_file(input_path)

    # Step 2: Convert equations to SSA
    ssa_equations = convert_to_ssa(equations)

    # Step 3: Build dependency graph
    dag = build_dag(ssa_equations)

    # Step 4: Generate ASAP schedule
    schedule = asap_schedule(dag)

    return {
        "input_file": str(input_path),
        "equations": equations,
        "ssa": ssa_equations,
        "dag": dag,
        "schedule": schedule,
    }


def main():
    parser = argparse.ArgumentParser(
        description="EC551 HLS Synthesizer"
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input equations file"
    )

    parser.add_argument(
        "--schedule",
        choices=["asap"],
        default="asap",
        help="Scheduling algorithm (currently ASAP)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print complete frontend results as JSON"
    )

    args = parser.parse_args()

    try:
        result = run_frontend(str(args.input_file))

    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("\n========== EC551 HLS SYNTHESIZER ==========")

    print(f"\nInput File: {result['input_file']}")
    print(f"Parsed Equations: {len(result['equations'])}")

    print("\n---------- SSA Equations ----------")

    for equation in result["ssa"]:
        print(
            f"{equation['result']} = "
            f"{equation['operand1']} "
            f"{equation['operator']} "
            f"{equation['operand2']}"
        )

    print("\n---------- ASAP Schedule ----------")

    for operation, cycle in sorted(
        result["schedule"].items(),
        key=lambda item: (item[1], item[0])
    ):
        print(f"Cycle {cycle}: {operation}")

    print("\nFrontend processing complete.")
    print("RTL generation is not connected yet.")


if __name__ == "__main__":
    main()