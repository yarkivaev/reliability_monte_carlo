"""Series-parallel fold of a source-sink reliability graph.

Usage:
    scheme(1, 2, {1: None, 2: None}, [(1, 2)])
"""

from collections import defaultdict

from reliability.formula import Atom, Infinite, Wire, Zero, combine


def walk(nodes, edges, source, sink):
    """Reject a cycle anywhere and a sink that source cannot reach."""
    exits = defaultdict(list)
    for origin, destination in edges:
        exits[origin].append(destination)
    state = {}
    def visit(node):
        marker = state.get(node)
        if marker == 0:
            raise ValueError(f"cycle visits {node!r} in the reliability graph")
        if marker == 1:
            return
        state[node] = 0
        for neighbor in exits[node]:
            visit(neighbor)
        state[node] = 1
    for node in nodes:
        visit(node)
    seen = set()
    stack = [source]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(exits[node])
    if sink not in seen:
        raise ValueError(f"sink {sink!r} is unreachable from source {source!r}")


def scheme(source, sink, nodes, edges):
    """Fold a source-sink graph into a lifetime formula with shared tails.

    Series contacts become min. Parallel leads with identical ends become max.
    A leftover bridge is evaluated as the longest remaining constrained path.
    """
    names = set(nodes)
    if source not in names:
        raise ValueError(f"source {source!r} is absent from nodes {names!r}")
    if sink not in names:
        raise ValueError(f"sink {sink!r} is absent from nodes {names!r}")
    for origin, destination in edges:
        if origin not in names or destination not in names:
            raise ValueError(f"edge {(origin, destination)!r} leaves the node set {names!r}")
    walk(nodes, edges, source, sink)
    wires = [Wire((node, 0), (node, 1), Atom(node)) for node in nodes]
    for origin, destination in edges:
        wires.append(Wire((origin, 1), (destination, 0), Infinite()))
    start = (source, 0)
    finish = (sink, 1)
    changed = True
    while changed:
        changed = False
        groups = defaultdict(list)
        for wire in wires:
            groups[(wire.origin, wire.destination)].append(wire)
        merged = []
        for pair, bundle in groups.items():
            if len(bundle) >= 2:
                changed = True
                merged.append(Wire(pair[0], pair[1], combine("max", [wire.formula for wire in bundle])))
            else:
                merged.extend(bundle)
        wires = merged
        if changed:
            continue
        entries = defaultdict(list)
        exits = defaultdict(list)
        for wire in wires:
            entries[wire.destination].append(wire)
            exits[wire.origin].append(wire)
        for contact in list(entries.keys() | exits.keys()):
            if contact == start or contact == finish:
                continue
            incoming = entries[contact]
            outgoing = exits[contact]
            if len(incoming) == 1 and len(outgoing) == 1 and incoming[0] is not outgoing[0]:
                left = incoming[0]
                right = outgoing[0]
                wires = [wire for wire in wires if wire is not left and wire is not right]
                wires.append(Wire(left.origin, right.destination, combine("min", [left.formula, right.formula])))
                changed = True
                break
    return reach(start, wires, finish)


def reach(start, wires, finish):
    """Evaluate leftover leads as the best source-sink path of mins."""
    exits = defaultdict(list)
    for wire in wires:
        exits[wire.origin].append(wire)
    memo = {}
    active = set()
    def descend(contact):
        if contact == finish:
            return Infinite()
        if contact in memo:
            return memo[contact]
        if contact in active:
            raise ValueError(f"cycle remains at contact {contact!r}")
        active.add(contact)
        options = [combine("min", [wire.formula, descend(wire.destination)]) for wire in exits[contact]]
        active.remove(contact)
        if not options:
            formula = Zero()
        else:
            formula = combine("max", options)
        memo[contact] = formula
        return formula
    return descend(start)
