"""Tests for reliability.formula junctions."""

import unittest

from reliability.formula import Atom, Infinite, Junction, combine


class FormulaTests(unittest.TestCase):
    """Min and max trees used by the folded scheme."""

    def test_combine_drops_an_infinite_wire_from_a_minimum(self):
        formula = combine("min", [Infinite(), Atom("α")])
        self.assertEqual(formula.evaluate({"α": 2.75}), 2.75, "min with an infinite wire does not collapse to the atom")

    def test_junction_counts_binary_gates_in_a_nested_tree(self):
        formula = Junction("min", [Atom(1), Junction("max", [Atom(2), Atom(3)])])
        self.assertEqual(formula.gates(), 2, "nested min/max tree undercounts binary gates")
