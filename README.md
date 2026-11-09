# EC551-HLS-Synthesizer
A simplified High-Level Synthesis (HLS) tool that converts arithmetic equations into scheduled Verilog RTL for FPGA implementation.


## Parser and SSA: Running and Testing

The HLS frontend consists of two modules:

- `parser.py`: Reads arithmetic equations from a text file and converts them into structured representations.
- `ssa.py`: Converts parsed equations into Static Single Assignment (SSA) form by assigning unique versions to variables.

Both modules are implemented in Python.

### 1. Input File

Create an input file at `inputs/equations.txt`.

Example:

```text
X=A+B
Y=X+A
Z=X-B
Q=B*Z
```

The parser supports:
- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Up to 20 equations
- Variable names containing letters, numbers, and underscores
- Optional whitespace

Each equation must contain exactly two operands and one operator.

### 2. Run the Parser

From the project root, execute:

```bash
python3 hls/parser.py inputs/equations.txt
```

Expected output:

```text
{'result': 'X', 'operand1': 'A', 'operator': '+', 'operand2': 'B'}
{'result': 'Y', 'operand1': 'X', 'operator': '+', 'operand2': 'A'}
{'result': 'Z', 'operand1': 'X', 'operator': '-', 'operand2': 'B'}
{'result': 'Q', 'operand1': 'B', 'operator': '*', 'operand2': 'Z'}
```

The parser returns a list of dictionaries containing:

- `result`: Destination variable
- `operand1`: First operand
- `operator`: Arithmetic operation
- `operand2`: Second operand

### 3. Run SSA Conversion

The SSA module converts each assignment into a uniquely indexed variable.

Execute:

```bash
python3 hls/ssa.py inputs/equations.txt
```

Expected output:

```text
X_1=A+B
Y_1=X_1+A
Z_1=X_1-B
Q_1=B*Z_1
```

Variables that have not previously been assigned are treated as primary inputs and retain their original names.

### 4. Test Variable Reassignment

SSA must correctly handle repeated assignments.

Example input:

```text
X=A+B
X=X+C
Y=X*D
X=Y-A
Z=X+B
```

Run:

```bash
python3 hls/ssa.py inputs/equations.txt
```

Expected output:

```text
X_1=A+B
X_2=X_1+C
Y_1=X_2*D
X_3=Y_1-A
Z_1=X_3+B
```

Each assignment creates a new version of its destination variable.

Operands reference the most recently assigned version.

### 5. Export SSA to a Text File

To export SSA equations using the default filename:

```bash
python3 hls/ssa.py inputs/equations.txt --export-ssa
```

This creates:

```text
ssa_output.txt
```

To specify a custom output filename:

```bash
python3 hls/ssa.py inputs/equations.txt --export-ssa ssa_result.txt
```

The exported file contains one SSA equation per line.

### 6. Run Parser Unit Tests

The parser includes unit tests implemented using Python's `unittest` framework.

Run:

```bash
python3 test/test_parser.py -v
```

Alternatively, discover and execute all tests:

```bash
python3 -m unittest discover -s test -p "test_*.py" -v
```

The parser tests verify:

- Addition, subtraction, and multiplication
- Whitespace handling
- Variable reassignment
- Invalid equation detection
- Empty input files
- Maximum equation count
- Correct error line numbers
- Missing input files

Expected result:

```text
Ran 11 tests in 0.00Xs

OK
```

DAG
test with 
python3 hls/dag.py inputs/equations.txt

python3 hls/dag.py inputs/equations.txt --export-dag dag.json

python3 test/test_dag.py -v

python3 -m unittest discover -s test -p "test_*.py" -v


ASAP Scheduling
python3 hls/scheduling/asap.py inputs/equations.txt

python3 test/test_asap.py -v

python3 -m unittest discover -s test -p "test_*.py" -v


## Verilog Arithmetic Unit Testing

The arithmetic functional units are implemented in Verilog:

- `rtl/adder.v` — 16-bit addition
- `rtl/subtractor.v` — 16-bit subtraction
- `rtl/multiplier.v` — 16-bit multiplication

The testbench `testbench/tb_arithmetic.v` instantiates all three RTL modules and verifies their outputs.

### 1. Install Icarus Verilog

On macOS, install Icarus Verilog using MacPorts:

```bash
sudo port install iverilog
```

Verify the installation:

```bash
iverilog -V
```

### 2. Compile the Testbench

From the project root, run:

```bash
iverilog -g2012 -s tb_arithmetic -o /tmp/tb_arithmetic.vvp rtl/adder.v rtl/subtractor.v rtl/multiplier.v testbench/tb_arithmetic.v
```

This compiles the three arithmetic RTL modules together with the testbench.

### 3. Run the Simulation

```bash
vvp /tmp/tb_arithmetic.vvp
```

Expected output:

```text
PASS: 333 arithmetic checks passed
```


iverilog -g2012 -s tb_arithmetic_unit \
-o /tmp/tb_arithmetic_unit.vvp \
rtl/adder.v \
rtl/subtractor.v \
rtl/multiplier.v \
rtl/arithmetic_unit.v \
testbench/tb_arithmetic_unit.v

vvp /tmp/tb_arithmetic_unit.vvp


for manual clock steppin
iverilog -g2012 -s tb_manual_clk_step \
-o /tmp/tb_manual_clk_step.vvp \
rtl/manual_clk_step.v \
testbench/tb_manual_clk_step.v

vvp /tmp/tb_manual_clk_step.vvp


### 4. Test Coverage

The testbench evaluates:

- 11 directed input combinations
- 100 random input combinations
- Addition, subtraction, and multiplication
- Zero operands
- Overflow and underflow
- 16-bit multiplication result truncation

Each input combination tests all three arithmetic modules.

Total checks:

```text
111 input combinations × 3 operations = 333 checks
```

All 333 checks passed using Icarus Verilog.

These tests verify the combinational functionality of the arithmetic units. FPGA synthesis, timing verification, and clocked datapath integration are separate steps.


python3 main.py inputs/equations.txt --json
python3 -m unittest discover -s test -p "test_*.py" -v

### 7. Frontend Processing Pipeline

```text
    equations.txt
          |
          v
      parser.py
          |
          v
   Parsed Equations
          |
          v
        ssa.py
          |
          v
    SSA Equations
          |
          v
     DAG Builder
          |
          v
      Scheduler
          |
          v
   Verilog Generator
```

               INPUT EQUATIONS
                      |
                      v
                 PARSER
                      |
                      v
                  SSA
                      |
                      v
                   DAG
                      |
                      v
              SCHEDULER
             /         \
          ASAP        ALAP
             \         /
              v       v
           RESOURCE BINDING
                   |
                   v
             RTL GENERATOR
                   |
                   v
        +-----------------------+
        | Generated Verilog RTL |
        |                       |
        | Arithmetic units      |
        | Registers             |
        | Multiplexers          |
        | Control FSM           |
        +-----------------------+
                   |
                   v
             SIMULATION
                   |
                   v
            FPGA IMPLEMENTATION


The parser and SSA modules use the same dictionary structure, allowing SSA output to be passed directly to the DAG builder.
Team Split
Paul — HLS Frontend & Hardware Support
	•	Input equation parser
	•	Single Static Assignment (SSA) conversion
	•	SSA text export
	•	DAG construction and dependency analysis
	•	Basic CLI
	•	ASAP scheduling
	•	Verilog arithmetic functional units
	•	FPGA manual clock stepping
	•	Functional-unit output selection
	•	Frontend and hardware module testing

Aaron — Scheduling & Hardware Generation
	•	Constrained ASAP scheduling
	•	ALAP and constrained ALAP scheduling
	•	Custom scheduling strategy
	•	Resource allocation and binding
	•	Automatic Verilog RTL generator
	•	Datapath generation (registers and multiplexers)
	•	Control FSM generation
	•	FPGA top-level integration
	•	Vivado synthesis and FPGA deployment
	•	Scheduler and RTL testing

Shared
	•	Define interfaces between modules
	•	End-to-end integration and debugging
	•	Testbench development and verification
	•	Final FPGA validation
	•	README documentation and 30-minute demo preparation



    EC551-HLS-Synthesizer/
│
├── main.py                 # Main CLI entry point
├── README.md
│
├── inputs/
│   └── equations.txt
│
├── hls/
│   ├── parser.py
│   ├── ssa.py
│   ├── dag.py
│   ├── scheduling/
│   │   ├── asap.py
│   │   ├── alap.py
│   │   └── ...
│   └── ...
│
├── rtl/
│   ├── adder.v
│   ├── subtractor.v
│   ├── multiplier.v
│   ├── arithmetic_unit.v
│   └── manual_clk_step.v
│
├── test/
│   └── ...
│
└── testbench/
    ├── tb_arithmetic.v
    ├── tb_arithmetic_unit.v
    └── tb_manual_clk_step.v