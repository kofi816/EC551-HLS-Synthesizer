# Scheduling algorithms for an arithmetic dependency DAG.
#
# Schedules map SSA result names to zero-based start cycles. Operations occupy
# one non-pipelined functional unit for their full latency (one cycle by default).
# Resource dictionaries use +, -, * keys; omitted types are unconstrained.
# ALAP bounds are completion deadlines, not last starting-cycle indices.

from pprint import pprint
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.dag import build_dag
from hls.parser import parse_file
from hls.ssa import convert_to_ssa
from hls.scheduling.asap import asap_schedule


def _prepare(dag, latencies, resources=None):
    # Set default limits and latencies, validate inputs, and compute ASAP starts.
    latencies = dict({"+": 1, "-": 1, "*": 1} if latencies is None else latencies)
    resources = dict({} if resources is None else resources)
    for operator, value in latencies.items():
        if operator not in ("+", "-", "*") or type(value) is not int or value < 1:
            raise ValueError("Latencies must be positive integers for +, -, *")
    for operator, value in resources.items():
        if operator not in ("+", "-", "*") or type(value) is not int or value < 0:
            raise ValueError("Resource limits must be nonnegative integers for +, -, *")
    for node in dag.values():
        operator = node["operator"]
        if operator not in ("+", "-", "*") or operator not in latencies:
            raise ValueError(f"Missing or unsupported operator latency: {operator}")
        if resources.get(operator) == 0:
            raise ValueError(f"No functional units available for {operator}")
    # Validate missing dependencies and cycles using ASAP scheduling.
    earliest = asap_schedule(dag, latencies)
    return latencies, resources, earliest


def _list_schedule(dag, latencies, resources, priority=None):
    # Assign ready operations to cycles while respecting unit availability and priority.
    pending = list(dag)
    schedule = {}
    cycle = 0
    while pending:
        ready = [name for name in pending if all(
            dep in schedule and schedule[dep] + latencies[dag[dep]["operator"]] <= cycle
            for dep in dag[name]["dependencies"]
        )]
        if priority is not None:
            ready.sort(key=lambda name: -priority[name])
        used = {operator: 0 for operator in latencies}
        for name, start in schedule.items():
            operator = dag[name]["operator"]
            if start + latencies[operator] > cycle:
                used[operator] += 1
        for name in ready:
            operator = dag[name]["operator"]
            if used[operator] < resources.get(operator, len(dag)):
                schedule[name] = cycle
                used[operator] += 1
                pending.remove(name)
        cycle += 1
    return {name: schedule[name] for name in dag}


def constrained_asap_schedule(dag, resources, latencies=None):
    # Schedule operations as early as available resources allow, in DAG insertion order.
    latencies, resources, _ = _prepare(dag, latencies, resources)
    return _list_schedule(dag, latencies, resources)


def _reverse(dag):
    # Reverse dependency edges so operations can be scheduled from outputs backward.
    reversed_dag = {
        name: {"operator": node["operator"], "dependencies": []}
        for name, node in dag.items()
    }
    for name, node in dag.items():
        for dep in node["dependencies"]:
            reversed_dag[dep]["dependencies"].append(name)
    return reversed_dag


def _backward(dag, latency_bound, latencies, resources):
    # Schedule the reversed DAG and convert its times into starts before a deadline.
    latencies, resources, _ = _prepare(dag, latencies, resources)
    if latency_bound is not None and (
        type(latency_bound) is not int or latency_bound < 0
    ):
        raise ValueError("latency_bound must be a nonnegative integer")
    reverse_schedule = _list_schedule(_reverse(dag), latencies, resources)
    required = max((reverse_schedule[name] + latencies[node["operator"]]
                    for name, node in dag.items()), default=0)
    bound = required if latency_bound is None else latency_bound
    if bound < required:
        raise ValueError(
            f"Backward list scheduling needs {required} cycles; bound is {bound}. "
            "For constrained scheduling this heuristic does not prove infeasibility."
        )
    return {name: bound - reverse_schedule[name] - latencies[node["operator"]]
            for name, node in dag.items()}


def alap_schedule(dag, latency_bound=None, latencies=None):
    # Schedule operations as late as possible before a given or critical-path deadline.
    return _backward(dag, latency_bound, latencies, None)


def constrained_alap_schedule(dag, resources, latency_bound=None, latencies=None):
    # Schedule operations backward from a deadline while respecting resource limits.
    #
    # Without a bound, use this heuristic's achieved makespan. With a bound,
    # reject if the heuristic cannot fit; this is not an optimal feasibility solver.
    return _backward(dag, latency_bound, latencies, resources)


def custom_schedule(dag, resources=None, latencies=None):
    # Prioritize ready operations with the longest remaining critical path.
    latencies, resources, _ = _prepare(dag, latencies, resources)
    reverse = _reverse(dag)
    reverse_starts = asap_schedule(reverse, latencies)
    priority = {name: reverse_starts[name] + latencies[node["operator"]]
                for name, node in dag.items()}
    return _list_schedule(dag, latencies, resources, priority)


def schedule_dag(dag, mode="asap", resources=None, latency_bound=None, latencies=None):
    # Common entry point; all modes return {operation: start_cycle}.
    if mode == "asap":
        latencies, _, _ = _prepare(dag, latencies)
        return asap_schedule(dag, latencies)
    if mode == "constrained_asap":
        return constrained_asap_schedule(dag, resources, latencies)
    if mode == "alap":
        return alap_schedule(dag, latency_bound, latencies)
    if mode == "constrained_alap":
        return constrained_alap_schedule(dag, resources, latency_bound, latencies)
    if mode == "custom":
        return custom_schedule(dag, resources, latencies)
    raise ValueError(f"Unknown scheduling mode: {mode}")


def _ask_integer(label, default, minimum=1):
    # Read an integer from the menu, retrying until a valid value is entered.
    while True:
        value = input(f"{label} [{default}]: ").strip()
        if not value:
            return default
        try:
            number = int(value)
            if number >= minimum:
                return number
        except ValueError:
            pass
        print(f"Enter a whole number of at least {minimum}.")


def _interactive_options():
    # Collect the input path, scheduling mode, and relevant limits through prompts.
    print("\nScheduler setup (press Enter to accept a default)")
    default_path = Path(__file__).resolve().parents[1] / "inputs" / "equations.txt"
    path = input(f"Input file [{default_path}]: ").strip() or str(default_path)
    modes = ["asap", "constrained_asap", "alap", "constrained_alap", "custom"]
    for number, mode in enumerate(modes, 1):
        print(f"  {number}. {mode.replace('_', ' ').upper()}")
    while True:
        choice = _ask_integer("Mode number", 1)
        if choice <= len(modes):
            mode = modes[choice - 1]
            break
        print("Choose a mode from 1 to 5.")
    resources = {}
    if mode in ("constrained_asap", "constrained_alap", "custom"):
        for operator, label in (("+", "adders"), ("-", "subtractors"), ("*", "multipliers")):
            resources[operator] = _ask_integer(f"Number of {label}", 1, 0)
    latency_bound = None
    if mode in ("alap", "constrained_alap"):
        print("Automatic deadline: use the backward scheduler's required cycle count.")
        latency_bound = _ask_integer("Completion deadline (cycles; Enter for automatic)",
                                     None, 0)
    return path, mode, resources, latency_bound


def main():
    # Collect menu choices, build the DAG from equations, and print the schedule.
    try:
        path, mode, resources, latency_bound = _interactive_options()
        dag = build_dag(convert_to_ssa(parse_file(path)))
        schedule = schedule_dag(dag, mode, resources, latency_bound)
    except (ValueError, OSError, KeyError, TypeError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    pprint(schedule, sort_dicts=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
