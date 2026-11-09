# EC551-HLS-Synthesizer
A simplified High-Level Synthesis (HLS) tool that converts arithmetic equations into scheduled Verilog RTL for FPGA implementation.

## Generate the design

1. Edit `inputs/equations.txt`. Put one equation on each line, with two variable
   operands and one operator (`+`, `-`, or `*`). Up to 20 equations are supported.
   For example, the current board demo uses:

   ```text
   X=A+B
   Y=C+D
   Z=X*Y
   W=Z-X
   OUT=W+Y
   ```

   The last equation supplies the final result. Variable reassignment is supported
   through SSA conversion. The UART board interface supports external inputs
   **A, B, C, D**. You may use more than four intermediate variables; additional
   external inputs such as E require extending the UART controller and wrapper.
   Use variable operands; numeric literals are not part of this equation format.

2. From the project root, run:

   ```powershell
   python hls/generator.py
   ```

   For the current demo, accept the default input file, select mode **2
   (constrained ASAP)**, enter **1** adder, **1** subtractor, and **1** multiplier,
   and accept the default output path. Other scheduling modes are also available;
   ALAP modes additionally prompt for a completion deadline.

3. The generator writes **only `output/generated_design.v`** by default. It does
   not generate or overwrite the reusable sources in `rtl/`.

All board inputs, stored values, and arithmetic results are **8-bit unsigned**
values, ranging from **0 to 255**. Arithmetic wraps modulo 256: `255 + 1` becomes
`0`, and `0 - 1` becomes `255`. Decimal display does not change the arithmetic width.

## Build and connect the FPGA

In Vivado, add `output/generated_design.v` and all `.v` design sources in `rtl/`:

- `fpga_uart_top.v`: reusable board wrapper; set **fpga_uart_top** as synthesis top.
- `uart_command.v`: command parser and decimal reply formatting.
- `uart_data_rx.v`, `uart_data_tx.v`: UART data transport.
- `uart_byte_rx.v`, `uart_byte_tx.v`: byte-level UART transport.
- `hls_adder.v`, `hls_subtractor.v`, `hls_multiplier.v`: reusable arithmetic units.

Use your board's constraints to assign these ports:

| Top-level port | Board connection |
|---|---|
| `clk` | 50 MHz oscillator |
| `uart_rx` | Incoming data from USB-UART TX |
| `uart_tx` | Outgoing data to USB-UART RX |
| `led[7:0]` | Optional final-result LEDs |

Connect a common ground and use UART logic levels compatible with your board.
Generate the bitstream and program the FPGA. The wrapper resets automatically
on programming; buttons and switches are not needed.

After changing equations or scheduling, rerun the generator, rebuild the bitstream,
and reprogram the FPGA. The reusable RTL files stay the same. After changing only
UART formatting, rebuild and reprogram; regenerating the core is unnecessary.

## UART input format

Open YAT or another serial terminal and select the COM port for your FPGA's
USB-UART adapter. Configure **9600 baud, 8 data bits, no parity, 1 stop bit,
no flow control**. In YAT, use **Str** mode and **Send Text (F3)**.

Send commands as **ASCII text**. Send each command
separately and **wait for its reply before sending the next one**. Spaces, CR,
and LF are ignored, so a terminal may append a line ending.

| Command | Meaning |
|---|---|
| `R` | Reset the computation and clear inputs A through D |
| `Addd`, `Bddd`, `Cddd`, `Dddd` | Load an input with exactly three decimal digits (`000` through `255`) |
| `S` | Start when idle; advance one scheduled cycle when busy |
| `G` | Start and run to completion, or finish a paused computation |
| `?` | Read current results and status |

Command letters are uppercase. Values require three decimal digits, including leading zeroes.
Inputs may only be changed while the computation is idle.

| Example command | Input value in decimal |
|---|---:|
| `A000` | A = 0 |
| `A010` | A = 10 |
| `A100` | A = 100 |
| `A255` | A = 255 |

For example, `A010` means A = **10**. Values above 255 and nondecimal
characters are rejected with `!`, leaving the input unchanged. Two-digit commands
such as `A10` are incomplete: the parser waits for a third digit. Send all three
digits before waiting for a reply.

## UART output format

Replies are ASCII text in this format, followed by CR/LF:

```text
<result> <final> <adder> <subtractor> <multiplier> <busy><done>
```

| Field | Meaning |
|---|---|
| `result` | `+` for success; `!` for an invalid command or an input update while busy |
| `final` | Value of the last equation |
| `adder` | Latest addition result |
| `subtractor` | Latest subtraction result |
| `multiplier` | Latest multiplication result |
| `busy` | `1` while a computation is in progress, including a paused run; otherwise `0` |
| `done` | `1` after completion, until reset or the next accepted start; otherwise `0` |

The four numeric result fields always contain **three decimal digits**, from
`000` through `255`, including leading zeroes. Status `00` means idle/not done,
`10` means busy/not done, and `01` means idle/done. Each reply is 22 bytes,
including spaces and CR/LF. Input-loading acknowledgments show computation
results, not the input value just loaded. Results from an earlier run can remain
visible until overwritten; use `done` to identify completion of the current run.

For the demo equations above, send these commands one at a time:

```text
R
A001
B002
C003
D004
G
```

The final reply is:

```text
+ 025 025 018 021 01
```

This means final result = **25**, latest addition = **25**, subtraction = **18**,
multiplication = **21**, busy = **0**, done = **1**.
For manual stepping with constrained ASAP and one unit per operator, send `S`
once to start, then five more times to execute the demo. Use `?` to inspect status.
Keep YAT in **Str** mode to read these decimal text replies; its **10** button
shows decimal character codes rather than converting the result fields.

## Additional test case

For the demo equations above, test **A = 10, B = 20, C = 3, D = 4**.
After programming the FPGA with the decimal-input UART controller, send each
command separately in YAT's **Str** mode, waiting for its reply:

```text
R
A010
B020
C003
D004
G
```

Expected computation:

```text
X   = A+B = 30
Y   = C+D = 7
Z   = X*Y = 210
W   = Z-X = 180
OUT = W+Y = 187
```

Expected final reply:

```text
+ 187 187 180 210 01
```

The fields mean success, final result **187**, latest addition **187**,
subtraction **180**, multiplication **210**, busy **0**, and done **1**.

## Reusable RTL interface and simulation

The wrapper connects fixed `in_A` through `in_D`, `final_result`, `debug_adder`,
`debug_subtractor`, and `debug_multiplier` core ports. Unused inputs are ignored;
unused operator debug outputs are zero. With multiple units of one operator,
its debug port shows the last operation in equation order executed in the latest
cycle containing that operator. The generator supports additional primary input
names for standalone cores, but the UART wrapper only drives A through D.

The supplied UART data modules use active-low `rst`. RX uses `DATA_WIDTH=8` for
variable-length ASCII commands; TX uses `DATA_WIDTH=176`, `MSB_FIRST=1` to send a
complete decimal reply in one request. Standalone multibyte RX supports both byte
orders and discards incomplete words after a timeout. Use positive byte-multiple
widths from 8 through 504 bits with these data modules.

Add testbenches as simulation sources, not synthesis sources:

- `test/rtl/tb_fpga_uart_top.v`: current five-equation demo, serial loading,
  decimal output formatting for all 256 values, decimal input boundaries,
  invalid input and busy-update rejection, run-to-completion, reset,
  manual stepping, and status. Update expected results and step counts when
  changing equations or scheduling.
- `test/rtl/tb_uart_data.v`: 32-bit loopback in both byte orders, repeated words,
  and partial-word timeout recovery.

Run Python tests from the project root:

```powershell
python -m unittest discover -s test -p "test_*.py" -v
```

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



