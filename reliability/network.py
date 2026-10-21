"""Vertex-weighted reliability graph.

Usage:
    Network(1, 2, {1: exponential(1.0), 2: exponential(1.0)}, [(1, 2)])
"""

from reliability.scheme import scheme


class Network:
    """Vertex-weighted reliability graph folded into a lifetime formula.

    Usage:
        Network(1, 2, {1: exponential(1.0), 2: exponential(1.0)}, [(1, 2)])
    """

    def __init__(self, source, sink, nodes, edges):
        self.graph = (source, sink, tuple(edges))
        self.nodes = dict(nodes)
        self.formula = scheme(source, sink, nodes, edges)

    def lifetime(self, times):
        """Return product lifetime for a fully specified time map."""
        return self.formula.evaluate(times)
