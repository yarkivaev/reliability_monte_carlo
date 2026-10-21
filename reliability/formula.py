"""Min/max lifetime formulas of a reliability network.

Usage:
    Junction("min", [Atom(1), Atom(2)]).evaluate({1: 3.0, 2: 5.0})
"""

import math
import re


def token(node):
    """Return a LaTeX tau subscript for a vertex name."""
    text = str(node)
    if re.fullmatch(r"[0-9]+", text):
        return f"\\tau_{{{text}}}"
    return f"\\tau_{{\\mathrm{{{text}}}}}"


class Atom:
    """Leaf of a lifetime formula: the lifetime of one vertex.

    Usage:
        Atom(3).evaluate({3: 4.5})
    """

    def __init__(self, node):
        self.node = node

    def evaluate(self, times):
        """Return the sampled lifetime of this vertex."""
        return times[self.node]

    def flatten(self, kind):
        """Return this leaf as a one-element list for any junction kind."""
        return [self]

    def atoms(self):
        """Return the single vertex stored in this leaf."""
        return [self.node]

    def gates(self):
        """Return zero: a leaf has no min or max."""
        return 0

    def latex(self):
        """Return this vertex as a tau subscript."""
        return token(self.node)


class Infinite:
    """Sentinel for a perfect wire that never fails.

    Usage:
        combine("min", [Infinite(), Atom(1)])
    """

    def __init__(self):
        self.bound = math.inf

    def evaluate(self, times):
        """Return positive infinity."""
        return self.bound

    def flatten(self, kind):
        """Drop from a min and absorb a max."""
        if kind == "min":
            return []
        return None

    def atoms(self):
        """Return no vertices."""
        return []

    def gates(self):
        """Return zero."""
        return 0

    def latex(self):
        """Return infinity."""
        return "\\infty"


class Zero:
    """Lifetime of a contact that cannot reach the sink.

    Usage:
        Zero().evaluate({})
    """

    def __init__(self):
        self.bound = 0.0

    def evaluate(self, times):
        """Return zero."""
        return self.bound

    def flatten(self, kind):
        """Keep this constant as a child of any junction."""
        return [self]

    def atoms(self):
        """Return no vertices."""
        return []

    def gates(self):
        """Return zero."""
        return 0

    def latex(self):
        """Return a literal zero."""
        return "0"


class Junction:
    """n-ary min or max over child formulas.

    Usage:
        Junction("min", [Atom(1), Atom(2)]).evaluate({1: 3.0, 2: 5.0})
    """

    def __init__(self, kind, children):
        self.kind = kind
        self.children = list(children)

    def evaluate(self, times):
        """Evaluate every child and reduce them with min or max."""
        values = [child.evaluate(times) for child in self.children]
        if self.kind == "min":
            return min(values)
        return max(values)

    def flatten(self, kind):
        """Unwrap children when the junction kind matches, else stay nested."""
        if self.kind == kind:
            return list(self.children)
        return [self]

    def atoms(self):
        """Return vertices of every child, left to right."""
        names = []
        for child in self.children:
            names.extend(child.atoms())
        return names

    def gates(self):
        """Return the binary min/max count in this subtree."""
        total = len(self.children) - 1
        for child in self.children:
            total += child.gates()
        return total

    def latex(self):
        """Return a flattened min or max in LaTeX."""
        body = ",".join(child.latex() for child in self.children)
        command = "\\min" if self.kind == "min" else "\\max"
        return f"{command}\\left({body}\\right)"


class Wire:
    """Directed lead between two contacts with a lifetime formula on it.

    Usage:
        Wire((1, 0), (1, 1), Atom(1))
    """

    def __init__(self, origin, destination, formula):
        self.origin = origin
        self.destination = destination
        self.formula = formula


def combine(kind, parts):
    """Build a flattened min or max, dropping or absorbing infinite wires."""
    children = []
    for part in parts:
        pieces = part.flatten(kind)
        if pieces is None:
            return Infinite()
        children.extend(pieces)
    if not children:
        return Infinite()
    if len(children) == 1:
        return children[0]
    return Junction(kind, children)
