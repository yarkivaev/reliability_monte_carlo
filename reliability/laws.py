"""Factories for vertex lifetime laws.

Usage:
    exponential(0.5)(random.Random(1))
"""

import ast
import math
import random


ALLOWED = {"rng", "math", "max", "min", "abs", "pow", "round"}


class Guard(ast.NodeVisitor):
    """Reject names and imports that a custom law must not use.

    Usage:
        Guard().visit(ast.parse("rng.gauss(1, 0)", mode="eval"))
    """

    def visit_Name(self, node):
        """Reject an identifier outside the allowed set."""
        if node.id not in ALLOWED:
            raise ValueError(f"custom law uses forbidden name {node.id!r}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Allow attributes only on rng or math."""
        target = node.value
        if not isinstance(target, ast.Name) or target.id not in {"rng", "math"}:
            raise ValueError(f"custom law reads attribute {node.attr!r} off a forbidden base")
        self.generic_visit(node)

    def visit_Import(self, node):
        """Reject an import."""
        raise ValueError("custom law contains an import")

    def visit_ImportFrom(self, node):
        """Reject a from-import."""
        raise ValueError("custom law contains an import")


def custom(source):
    """Return a draw from a restricted Python expression over rng.

    Usage:
        custom("max(0.0, rng.gauss(90.0, 8.0))")(random.Random(1))
    """
    tree = ast.parse(source, mode="eval")
    Guard().visit(tree)
    code = compile(tree, "<law>", "eval")
    namespace = {"max": max, "min": min, "abs": abs, "pow": pow, "round": round, "math": math}
    def draw(rng):
        return eval(code, {"__builtins__": {}}, {**namespace, "rng": rng})
    probe = draw(random.Random(0))
    if probe != probe or probe is None:
        raise ValueError(f"custom law {source!r} did not yield a number")
    return draw


def exponential(rate):
    """Return a draw from the exponential law with the given rate.

    Usage:
        exponential(0.5)(random.Random(1))
    """
    def draw(rng):
        return rng.expovariate(rate)
    return draw


def normal(center, scale):
    """Return a draw from the normal law with the given center and scale.

    Usage:
        normal(10.0, 2.0)(random.Random(1))
    """
    def draw(rng):
        return rng.gauss(center, scale)
    return draw


def truncated_normal(center, scale, low=0.0):
    """Return a draw from the normal law rejected below low.

    Usage:
        truncated_normal(8.0, 3.0, low=0.0)(random.Random(1))
    """
    def draw(rng):
        sample = rng.gauss(center, scale)
        while sample < low:
            sample = rng.gauss(center, scale)
        return sample
    return draw
