# EC551-HLS-Synthesizer
A simplified High-Level Synthesis (HLS) tool that converts arithmetic equations into scheduled Verilog RTL for FPGA implementation.


parser.py takes input equations and return
[
    {"result": "X", "operand1": "A", "operator": "+", "operand2": "B"},
    {"result": "Y", "operand1": "X", "operator": "+", "operand2": "A"},
    {"result": "Z", "operand1": "X", "operator": "-", "operand2": "B"},
    {"result": "Q", "operand1": "B", "operator": "*", "operand2": "Z"}
]

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



