# Allocate non-pipelined arithmetic units and bind scheduled operations to them.
# Units are occupied over [start, start + latency), so a unit can be reused
# exactly when its previous operation finishes. Omitted resource limits are unlimited.

from pprint import pprint
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls.scheduling.asap import asap_schedule


def _validate_schedule(dag, schedule, latencies, resources):
    # Reject invalid graphs, timings, dependencies, latencies, and resource limits.
    if set(schedule) != set(dag):
        raise ValueError("Schedule must contain exactly the DAG operation names")
    for operator, latency in latencies.items():
        if operator not in ("+", "-", "*") or type(latency) is not int or latency < 1:
            raise ValueError("Latencies must be positive integers for +, -, *")
    for operator, count in resources.items():
        if operator not in ("+", "-", "*") or type(count) is not int or count < 0:
            raise ValueError("Resource limits must be nonnegative integers for +, -, *")
    for name, node in dag.items():
        if node["operator"] not in ("+", "-", "*"):
            raise ValueError(f"Unsupported operator: {node['operator']}")
        if type(schedule[name]) is not int or schedule[name] < 0:
            raise ValueError(f"Start cycle for {name} must be a nonnegative integer")
    asap_schedule(dag, latencies)
    for name, node in dag.items():
        for dependency in node["dependencies"]:
            finish = schedule[dependency] + latencies[dag[dependency]["operator"]]
            if schedule[name] < finish:
                raise ValueError(f"{name} starts before {dependency} finishes")


def bind_resources(dag, schedule, resources=None, latencies=None):
    # Assign operations to reusable units and return bindings, unit details, and counts.
    resources = dict({} if resources is None else resources)
    latencies = dict({"+": 1, "-": 1, "*": 1} if latencies is None else latencies)
    _validate_schedule(dag, schedule, latencies, resources)

    prefixes = {"+": "adder", "-": "subtractor", "*": "multiplier"}
    pools = {operator: [] for operator in prefixes}
    available = {}
    units = {}
    binding = {}

    # Earliest-start interval allocation uses the minimum units for a fixed schedule.
    # Stable sorting preserves DAG order for operations starting together.
    for name in sorted(dag, key=lambda operation: schedule[operation]):
        operator = dag[name]["operator"]
        start = schedule[name]
        unit = next((unit for unit in pools[operator] if available[unit] <= start), None)

        if unit is None:
            index = len(pools[operator])
            if index >= resources.get(operator, len(dag)):
                raise ValueError(
                    f"Insufficient {prefixes[operator]} units at cycle {start}: "
                    f"cannot bind {name}; reschedule with the resource limit"
                )
            unit = f"{prefixes[operator]}_{index}"
            pools[operator].append(unit)
            units[unit] = {"operator": operator, "operations": []}

        binding[name] = unit
        units[unit]["operations"].append(name)
        available[unit] = start + latencies[operator]

    return {
        "binding": {name: binding[name] for name in dag},
        "units": units,
        "resource_counts": {operator: len(pool) for operator, pool in pools.items()},
    }


def main():
    # Collect menu choices, schedule the equations, and display resource bindings.
    from hls.dag import build_dag
    from hls.parser import parse_file
    from hls.ssa import convert_to_ssa
    from hls.scheduler import _interactive_options, schedule_dag

    try:
        path, mode, resources, latency_bound = _interactive_options()
        dag = build_dag(convert_to_ssa(parse_file(path)))
        schedule = schedule_dag(dag, mode, resources, latency_bound)
        result = bind_resources(dag, schedule, resources)
    except (ValueError, OSError, KeyError, TypeError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("\nSchedule (operation -> start cycle):")
    pprint(schedule, sort_dicts=False)
    print("\nBinding (operation -> functional unit):")
    pprint(result["binding"], sort_dicts=False)
    print("\nFunctional units and assigned operations:")
    pprint(result["units"], sort_dicts=False)
    print("\nAllocated hardware counts:")
    for operator, label in (("+", "Adders"), ("-", "Subtractors"), ("*", "Multipliers")):
        print(f"  {label}: {result['resource_counts'][operator]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
