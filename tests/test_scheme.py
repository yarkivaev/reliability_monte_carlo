"""Tests for reliability.scheme folding."""

import random
import unittest

from reliability.scheme import scheme


def textbook():
    """Return source, sink and edges of the seven-element figure."""
    return (
        1,
        7,
        [(1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 6), (5, 7), (6, 7)],
    )


def paths(times):
    """Return lifetime of the figure as the longest of its three chains."""
    return max(
        min(times[1], times[2], times[5], times[7]),
        min(times[1], times[3], times[5], times[7]),
        min(times[1], times[4], times[6], times[7]),
    )


def book(times):
    """Return the printed formula that misplaces τ5 and τ7."""
    return min(
        times[1],
        max(
            min(times[4], times[6]),
            min(max(times[2], times[3], times[5]), times[7]),
        ),
    )


class SchemeTests(unittest.TestCase):
    """Lifetime formula built by series-parallel folding."""

    def test_scheme_matches_the_three_chains_on_irregular_times(self):
        source, sink, edges = textbook()
        times = {node: random.Random(node * 97 + 13).random() * 17.3 + 0.41 for node in range(1, 8)}
        formula = scheme(source, sink, {node: None for node in times}, edges)
        self.assertEqual(formula.evaluate(times), paths(times), "folded lifetime diverges from the longest chain")

    def test_scheme_keeps_each_figure_element_once(self):
        source, sink, edges = textbook()
        formula = scheme(source, sink, {node: None for node in range(1, 8)}, edges)
        self.assertEqual(sorted(formula.atoms()), list(range(1, 8)), "folded figure repeats or drops an element")

    def test_scheme_uses_six_binary_gates_on_the_figure(self):
        source, sink, edges = textbook()
        formula = scheme(source, sink, {node: None for node in range(1, 8)}, edges)
        self.assertEqual(formula.gates(), 6, "folded figure is not the shortest series-parallel tree")

    def test_scheme_disagrees_with_the_printed_brackets_when_tau_five_is_zero(self):
        source, sink, edges = textbook()
        times = {1: 10.7, 2: 80.2, 3: 3.1, 4: 8.4, 5: 0.0, 6: 9.9, 7: 50.5}
        formula = scheme(source, sink, {node: None for node in times}, edges)
        self.assertNotEqual(formula.evaluate(times), book(times), "folded lifetime copies the printed brackets")

    def test_scheme_still_matches_the_chains_when_tau_five_is_zero(self):
        source, sink, edges = textbook()
        times = {1: 10.7, 2: 80.2, 3: 3.1, 4: 8.4, 5: 0.0, 6: 9.9, 7: 50.5}
        formula = scheme(source, sink, {node: None for node in times}, edges)
        self.assertEqual(formula.evaluate(times), paths(times), "folded lifetime dies with the upper branch")

    def test_scheme_matches_bridge_paths_on_irregular_times(self):
        edges = [(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 6), (2, 5)]
        times = {node: random.Random(node * 53 + 7).random() * 11.9 + 0.23 for node in range(1, 7)}
        formula = scheme(1, 6, {node: None for node in times}, edges)
        longest = max(
            min(times[1], times[2], times[4], times[6]),
            min(times[1], times[3], times[5], times[6]),
            min(times[1], times[2], times[5], times[6]),
        )
        self.assertEqual(formula.evaluate(times), longest, "bridge lifetime diverges from the longest path")

    def test_scheme_keeps_each_bridge_element_once(self):
        edges = [(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 6), (2, 5)]
        formula = scheme(1, 6, {node: None for node in range(1, 7)}, edges)
        self.assertEqual(sorted(set(formula.atoms())), list(range(1, 7)), "bridge formula drops an element")

    def test_scheme_folds_non_ascii_names_as_a_single_lead(self):
        formula = scheme("α", "ω", {"α": None, "ω": None}, [("α", "ω")])
        times = {"α": 4.25, "ω": 1.75}
        self.assertEqual(formula.evaluate(times), 1.75, "two named vertices do not fold into their minimum")

    def test_scheme_rejects_a_cycle(self):
        self.assertRaises(ValueError, scheme, 1, 2, {1: None, 2: None}, [(1, 2), (2, 1)])

    def test_scheme_rejects_a_missing_source_sink_path(self):
        self.assertRaises(ValueError, scheme, 1, 3, {1: None, 2: None, 3: None}, [(1, 2)])

    def test_scheme_rejects_an_edge_outside_the_node_set(self):
        self.assertRaises(ValueError, scheme, 1, 1, {1: None}, [(1, 2)])
