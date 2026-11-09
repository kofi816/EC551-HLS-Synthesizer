# Generate a synchronous datapath and control FSM for one-cycle arithmetic units.
# All values are unsigned WIDTH-bit vectors; arithmetic wraps modulo 2**WIDTH.

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.binding import bind_resources
from hls.dag import build_dag, get_primary_inputs
from hls.parser import parse_file
from hls.ssa import convert_to_ssa
from hls.scheduler import _interactive_options, schedule_dag


def _validate_binding(dag, schedule, allocation):
    # Check that supplied unit assignments match operators and never overlap.
    assignments = allocation["binding"]
    units = allocation["units"]
    if set(assignments) != set(dag):
        raise ValueError("Binding must contain exactly the DAG operation names")
    occupied = set()
    for name, unit in assignments.items():
        if unit not in units or units[unit]["operator"] != dag[name]["operator"]:
            raise ValueError(f"Invalid functional unit for {name}")
        slot = (unit, schedule[name])
        if slot in occupied:
            raise ValueError(f"Unit {unit} has overlapping operations")
        occupied.add(slot)


def generate_verilog(dag, schedule, allocation=None, width=16, latencies=None):
    # Return the scheduled datapath and FSM, referencing separate arithmetic modules.
    if not dag:
        raise ValueError("Cannot generate a design without operations")
    if type(width) is not int or width < 1:
        raise ValueError("Width must be a positive integer")
    if latencies is not None and any(
        type(value) is not int or value != 1 for value in latencies.values()
    ):
        raise ValueError("RTL generation currently supports only one-cycle operations")
    # Validate schedule dependencies, cycle numbers, and graph structure.
    inferred = bind_resources(dag, schedule, latencies=latencies)
    allocation = inferred if allocation is None else allocation
    _validate_binding(dag, schedule, allocation)
    inputs = get_primary_inputs(dag)
    for name in list(dag) + inputs:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid signal identifier: {name}")
    for name, node in dag.items():
        operands = node["operands"]
        if len(operands) != 2 or set(node["dependencies"]) != {
            operand for operand in operands if operand in dag
        }:
            raise ValueError(f"Invalid operands or dependencies for {name}")

    # Prefix external ports and use numeric internal names to avoid name collisions.
    values = {name: f"value_{index}" for index, name in enumerate(dag)}
    captured = {name: f"input_{index}" for index, name in enumerate(inputs)}
    sources = {**captured, **values}
    unit_ids = {unit: f"fu_{index}" for index, unit in enumerate(allocation["units"])}
    cycles = max(schedule.values(), default=-1) + 1
    lines = [
        "// Generated unsigned arithmetic datapath and control FSM.",
        "// Inputs are captured on start while idle; outputs remain valid until overwritten.",
        "// done stays high until reset or the next accepted start.",
        f"module generated_design #(parameter WIDTH = {width}) (",
    ]
    ports = ["input wire clk", "input wire reset", "input wire start", "input wire step",
             "output reg busy", "output reg done"]
    ports += [f"output reg [WIDTH-1:0] debug_{signal}" for signal in unit_ids.values()]
    ports += [f"input wire [WIDTH-1:0] in_{name}" for name in sorted(set(inputs) | {"A", "B", "C", "D"})]
    ports += ["output wire [WIDTH-1:0] final_result"]
    ports += [f"output reg [WIDTH-1:0] debug_{name}" for name in ("adder", "subtractor", "multiplier")]
    # Expose all SSA values for debugging and final-output selection by the board wrapper.
    ports += [f"output wire [WIDTH-1:0] out_{name}" for name in dag]
    lines += ["    " + port + ("," if i < len(ports)-1 else "")
              for i, port in enumerate(ports)]
    lines += [");", "localparam IDLE = 0;", f"localparam FINISH = {cycles + 1};",
              f"reg [{max(1, (cycles + 1).bit_length()) - 1}:0] state;"]
    for signal in list(captured.values()) + list(values.values()):
        lines.append(f"reg [WIDTH-1:0] {signal};")
    lines.append(f"assign final_result = {values[list(dag)[-1]]};")
    for name, signal in values.items():
        lines.append(f"assign out_{name} = {signal};")
    debug_names = {"+": "adder", "-": "subtractor", "*": "multiplier"}
    module_names = {"+": "hls_adder", "-": "hls_subtractor", "*": "hls_multiplier"}
    for unit, detail in allocation["units"].items():
        signal = unit_ids[unit]
        lines += [f"reg [WIDTH-1:0] {signal}_a;",
                  f"reg [WIDTH-1:0] {signal}_b;",
                  f"wire [WIDTH-1:0] {signal}_result;",
                  f"{module_names[detail['operator']]} #(.WIDTH(WIDTH)) {signal} (",
                  f"    .a({signal}_a), .b({signal}_b), .result({signal}_result));"]
    if unit_ids:
        lines += ["", "// FSM-controlled operand multiplexers.", "always @(*) begin"]
        for signal in unit_ids.values():
            lines += [f"    {signal}_a = 0;", f"    {signal}_b = 0;"]
        lines.append("    case (state)")
        for cycle in sorted(set(schedule.values())):
            lines.append(f"        {cycle + 1}: begin")
            for name, node in dag.items():
                if schedule[name] == cycle:
                    signal = unit_ids[allocation["binding"][name]]
                    left, right = node["operands"]
                    lines += [f"            {signal}_a = {sources[left]};",
                              f"            {signal}_b = {sources[right]};"]
            lines.append("        end")
        lines += ["        default: begin end", "    endcase", "end"]
    lines += ["", "// State-dependent assignments provide register write enables.",
              "always @(posedge clk) begin", "    if (reset) begin",
              "        state <= IDLE;", "        busy <= 0;", "        done <= 0;"]
    for signal in list(captured.values()) + list(values.values()):
        lines.append(f"        {signal} <= 0;")
    for signal in list(unit_ids.values()) + list(debug_names.values()):
        lines.append(f"        debug_{signal} <= 0;")
    lines += ["    end else begin", "        case (state)",
              "            IDLE: begin", "                if (start) begin",
              "                    busy <= 1;", "                    done <= 0;",
              "                    state <= 1;"]
    for name, signal in captured.items():
        lines.append(f"                    {signal} <= in_{name};")
    for signal in list(unit_ids.values()) + list(debug_names.values()):
        lines.append(f"                    debug_{signal} <= 0;")
    lines += ["                end", "            end"]
    for cycle in range(cycles):
        lines.append(f"            {cycle + 1}: if (step) begin")
        for name in dag:
            if schedule[name] == cycle:
                signal = unit_ids[allocation["binding"][name]]
                lines.append(f"                {values[name]} <= {signal}_result;")
                lines.append(f"                debug_{signal} <= {signal}_result;")
                lines.append(f"                debug_{debug_names[dag[name]['operator']]} <= {signal}_result;")
        if cycle == cycles - 1:
            lines += ["                busy <= 0;", "                done <= 1;"]
        lines += [f"                state <= {cycle + 2};", "            end"]
    lines += ["            FINISH: begin", "                busy <= 0;",
              "                done <= 1;", "                if (!start) state <= IDLE;",
              "            end", "            default: begin",
              "                state <= IDLE;", "                busy <= 0;",
              "                done <= 0;", "            end", "        endcase",
              "    end", "end", "endmodule"]
    return "\n".join(lines) + "\n"


def main():
    # Collect menu choices and write only the equation-dependent core.
    try:
        path, mode, resources, bound = _interactive_options()
        width = 8
        default = Path(__file__).resolve().parents[1] / "output" / "generated_design.v"
        output = Path(input(f"Output Verilog file [{default}]: ").strip() or default)
        equations = parse_file(path)
        dag = build_dag(convert_to_ssa(equations))
        schedule = schedule_dag(dag, mode, resources, bound)
        allocation = bind_resources(dag, schedule, resources)
        source = generate_verilog(dag, schedule, allocation, width)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(source, encoding="utf-8")
    except (ValueError, OSError, KeyError, TypeError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Generated Verilog: {output}")
    print("Reusable support modules: rtl/ (add these separately to the FPGA project)")
    final_equation = equations[-1]
    print(f"Output equation: {final_equation['result']} = "
          f"{final_equation['operand1']} {final_equation['operator']} {final_equation['operand2']}")
    print(f"Output signal: final_result (from {list(dag)[-1]}, unsigned {width}-bit)")
    print(f"Primary inputs: {', '.join(get_primary_inputs(dag))}")
    print(f"Execution cycles: {max(schedule.values()) + 1} (after start)")
    print("Numeric result: load inputs over UART, then send G; read the first numeric reply field")
    print("FPGA synthesis top: fpga_uart_top (rtl/fpga_uart_top.v)")
    print(f"Hardware counts: {allocation['resource_counts']}")
    print("Board ports: clk, uart_rx, uart_tx, led[7:0]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
