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



