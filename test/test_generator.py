import copy
import sys
import unittest
from pathlib import Path

# Support running this test file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.binding import bind_resources
from hls.dag import build_dag
from hls.generator import generate_verilog, main
from unittest.mock import patch
from tempfile import TemporaryDirectory
from hls.parser import parse_file, parse_line
from hls.scheduler import schedule_dag
from hls.ssa import convert_to_ssa


class TestGenerator(unittest.TestCase):
    def setUp(self):
        # Prepare a dependency chain that reuses one adder.
        self.dag = build_dag(convert_to_ssa([
            parse_line("X=A+B", 1), parse_line("Y=X+C", 2)]))
        self.schedule = schedule_dag(self.dag)

    def test_shared_adder_and_capture(self):
        # Check that unit sharing, input capture, and result registers are emitted.
        original = copy.deepcopy((self.dag, self.schedule))
        source = generate_verilog(self.dag, self.schedule, width=8)
        self.assertEqual(source.count("hls_adder #(.WIDTH(WIDTH))"), 1)
        self.assertIn("input_0 <= in_A;", source)
        self.assertIn("fu_0_a = value_0;", source)
        self.assertIn("value_0 <= fu_0_result;", source)
        self.assertIn("value_1 <= fu_0_result;", source)
        self.assertIn("assign out_Y_1 = value_1;", source)
        self.assertIn("parameter WIDTH = 8", source)
        self.assertEqual((self.dag, self.schedule), original)

    def test_all_modes_with_workspace_equations(self):
        # Check generation for the larger example under every scheduler mode.
        path = Path(__file__).resolve().parents[1] / "inputs" / "equations.txt"
        dag = build_dag(convert_to_ssa(parse_file(path)))
        limits = {"+": 1, "-": 1, "*": 1}
        for mode in ("asap", "alap", "constrained_asap", "constrained_alap", "custom"):
            with self.subTest(mode=mode):
                schedule = schedule_dag(dag, mode, limits)
                resources = limits if mode in ("constrained_asap", "constrained_alap", "custom") else None
                allocation = bind_resources(dag, schedule, resources)
                source = generate_verilog(dag, schedule, allocation)
                for name in dag:
                    self.assertIn(f"assign out_{name} =", source)
                for cycle in range(max(schedule.values()) + 1):
                    self.assertIn(f"state <= {cycle + 2};", source)

    def test_reject_invalid_inputs(self):
        # Reject unsupported widths, latencies, and dependency timing.
        for width in (0, -1, True, 1.5):
            with self.subTest(width=width), self.assertRaises(ValueError):
                generate_verilog(self.dag, self.schedule, width=width)
        with self.assertRaises(ValueError):
            generate_verilog(self.dag, self.schedule, latencies={"+": 2})
        with self.assertRaises(ValueError):
            generate_verilog(self.dag, {"X_1": 0, "Y_1": 0})
        with self.assertRaises(ValueError):
            generate_verilog({}, {})

    def test_reject_overlapping_binding(self):
        # Detect a hand-edited allocation that puts parallel operations on one unit.
        dag = copy.deepcopy(self.dag)
        dag["Y_1"]["operands"] = ["A", "C"]
        dag["Y_1"]["dependencies"] = []
        schedule = {"X_1": 0, "Y_1": 0}
        allocation = bind_resources(dag, schedule)
        allocation["binding"]["Y_1"] = allocation["binding"]["X_1"]
        with self.assertRaises(ValueError):
            generate_verilog(dag, schedule, allocation)

    def test_manual_step_and_display_registers(self):
        # Check that steps gate execution and debug values update only with results.
        allocation = bind_resources(self.dag, self.schedule)
        source = generate_verilog(self.dag, self.schedule, allocation, width=8)
        self.assertIn("input wire step", source)
        self.assertIn("1: if (step) begin", source)
        self.assertIn("2: if (step) begin", source)
        self.assertEqual(source.count("debug_fu_0 <= fu_0_result;"), 2)
    def test_fixed_board_interface(self):
        source = generate_verilog(self.dag, self.schedule)
        for name in ("A", "B", "C", "D"):
            self.assertIn(f"input wire [WIDTH-1:0] in_{name}", source)
        self.assertIn("assign final_result = value_1;", source)
        for name in ("adder", "subtractor", "multiplier"):
            self.assertIn(f"debug_{name} <= 0;", source)
        self.assertIn("debug_adder <= fu_0_result;", source)

    def test_cli_writes_only_design_and_preserves_support(self):
        equations = Path(__file__).resolve().parents[1] / "inputs/equations.txt"
        with TemporaryDirectory() as directory:
            target = Path(directory)
            support = target / "uart_data_tx.v"
            support.write_text("existing reusable RTL")
            with patch("hls.generator._interactive_options", return_value=(str(equations), "constrained_asap", {"+": 1, "-": 1, "*": 1}, None)), patch("builtins.input", return_value=str(target / "generated_design.v")):
                self.assertEqual(main(), 0)
            self.assertEqual({p.name for p in target.iterdir()}, {"generated_design.v", "uart_data_tx.v"})
            self.assertEqual(support.read_text(), "existing reusable RTL")


if __name__ == "__main__":
    unittest.main()
