"""Layout, LaTeX and histogram helpers for a reliability network.

Usage:
    latex(scheme(1, 2, {1: None, 2: None}, [(1, 2)]))
"""

from collections import defaultdict, deque


def latex(formula):
    """Return the folded lifetime as a LaTeX assignment for xi."""
    return f"\\xi={formula.latex()}"


def layers(source, names, edges):
    """Return BFS layers from source, with unreachable names on the right.

    Usage:
        layers(1, [1, 2, 3], [(1, 2), (1, 3)])
    """
    exits = defaultdict(list)
    for origin, destination in edges:
        exits[origin].append(destination)
    rank = {source: 0}
    seen = {source: 0}
    queue = deque([source])
    stamp = 1
    while queue:
        node = queue.popleft()
        for neighbor in exits[node]:
            if neighbor in rank:
                continue
            rank[neighbor] = rank[node] + 1
            seen[neighbor] = stamp
            stamp += 1
            queue.append(neighbor)
    ceiling = max(rank.values(), default=0)
    stacked = defaultdict(list)
    for name in names:
        depth = rank.get(name, ceiling + 1)
        if name not in seen:
            seen[name] = stamp
            stamp += 1
        stacked[depth].append(name)
    for depth in stacked:
        stacked[depth].sort(key=lambda name: seen[name])
    return [stacked[depth] for depth in sorted(stacked)]


def parts(names, edges):
    """Return weakly connected name groups in name order.

    Usage:
        parts([1, 2, 3], [(1, 2)])
    """
    parent = {name: name for name in names}
    def find(name):
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name
    for origin, destination in edges:
        if origin not in parent or destination not in parent:
            continue
        left = find(origin)
        right = find(destination)
        if left != right:
            parent[right] = left
    groups = []
    index = {}
    for name in names:
        head = find(name)
        if head not in index:
            index[head] = len(groups)
            groups.append([])
        groups[index[head]].append(name)
    return groups


def root(names, edges, preferred):
    """Return the BFS start of a weak component.

    Usage:
        root([8, 9], [(8, 9)], 1)
    """
    if preferred in names:
        return preferred
    members = set(names)
    inbound = {name: 0 for name in names}
    for origin, destination in edges:
        if origin in members and destination in members:
            inbound[destination] += 1
    for name in names:
        if inbound[name] == 0:
            return name
    return names[0]


def places(source, names, edges):
    """Return unit-square centers, stacking weakly connected components.

    Usage:
        places(1, [1, 2, 8, 9], [(1, 2), (8, 9)])
    """
    groups = parts(names, edges)
    lead = next((group for group in groups if source in group), None)
    rows = ([lead] if lead is not None else []) + [group for group in groups if group is not lead]
    count = max(len(rows), 1)
    points = {}
    inset = 0.12
    for index, group in enumerate(rows):
        members = set(group)
        local = [(origin, destination) for origin, destination in edges if origin in members and destination in members]
        stacked = layers(root(group, edges, source), group, local)
        span = max(len(stacked) - 1, 1)
        for column, layer in enumerate(stacked):
            height = len(layer)
            for row, name in enumerate(layer):
                across = column / span
                down = 0.5 if height == 1 else row / (height - 1)
                rise = down if count == 1 else (index + inset + (1 - 2 * inset) * down) / count
                points[name] = {"x": across, "y": rise}
    return points


def bins(samples, count=24):
    """Return equal-width histogram bins for a lifetime sample."""
    if count < 1:
        raise ValueError(f"bin count {count} is below 1")
    if not samples:
        return []
    low = min(samples)
    high = max(samples)
    if low == high:
        return [{"start": low, "stop": high, "count": len(samples)}]
    width = (high - low) / count
    totals = [0] * count
    for sample in samples:
        index = min(int((sample - low) / width), count - 1)
        totals[index] += 1
    return [
        {"start": low + index * width, "stop": low + (index + 1) * width, "count": totals[index]}
        for index in range(count)
    ]
