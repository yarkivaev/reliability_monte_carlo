"""Tests for reliability.display."""

import unittest

from reliability.display import bins, latex, layers, places
from reliability.formula import Atom, Junction
from reliability.scheme import scheme


def textbook():
    """Return source, names and edges of the seven-element figure."""
    return (
        1,
        list(range(1, 8)),
        [(1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 6), (5, 7), (6, 7)],
    )


class DisplayTests(unittest.TestCase):
    """LaTeX, BFS layers and histogram bins."""

    def test_layers_follow_the_figure_columns(self):
        source, names, edges = textbook()
        self.assertEqual(layers(source, names, edges), [[1], [2, 3, 4], [5, 6], [7]], "figure layers leave the assignment drawing")

    def test_latex_keeps_every_figure_tau(self):
        source, names, edges = textbook()
        source_tex = latex(scheme(source, 7, {node: None for node in names}, edges))
        missing = [node for node in names if f"\\tau_{{{node}}}" not in source_tex]
        self.assertEqual(missing, [], "folded LaTeX drops a figure element")

    def test_latex_is_the_folded_assignment(self):
        source, names, edges = textbook()
        expected = "\\xi=\\min\\left(\\tau_{1},\\max\\left(\\min\\left(\\max\\left(\\tau_{2},\\tau_{3}\\right),\\tau_{5}\\right),\\min\\left(\\tau_{4},\\tau_{6}\\right)\\right),\\tau_{7}\\right)"
        self.assertEqual(latex(scheme(source, 7, {node: None for node in names}, edges)), expected, "folded LaTeX is not the assignment formula")

    def test_latex_typesets_a_named_atom(self):
        formula = Junction("min", [Atom("α"), Atom("ω")])
        self.assertEqual(latex(formula), "\\xi=\\min\\left(\\tau_{\\mathrm{α}},\\tau_{\\mathrm{ω}}\\right)", "named vertices do not become tau subscripts")

    def test_bins_stack_identical_samples_in_one_bar(self):
        value = 4.25
        self.assertEqual(bins([value, value, value], count=8), [{"start": value, "stop": value, "count": 3}], "constant sample still splits across bins")

    def test_bins_split_a_range_into_the_asked_count(self):
        self.assertEqual(len(bins([0.0, 1.5, 3.0, 4.5], count=3)), 3, "bin count does not follow the asked split")

    def test_layers_push_an_unreachable_name_to_the_right(self):
        self.assertEqual(layers(1, [1, 2, 9], [(1, 2)]), [[1], [2], [9]], "unreachable vertex stays in the source column")

    def test_places_keep_the_figure_on_a_unit_square(self):
        source, names, edges = textbook()
        self.assertEqual(
            places(source, names, edges),
            {
                1: {"x": 0.0, "y": 0.5},
                2: {"x": 1 / 3, "y": 0.0},
                3: {"x": 1 / 3, "y": 0.5},
                4: {"x": 1 / 3, "y": 1.0},
                5: {"x": 2 / 3, "y": 0.0},
                6: {"x": 2 / 3, "y": 1.0},
                7: {"x": 1.0, "y": 0.5},
            },
            "figure places leave the layered drawing",
        )

    def test_places_stretch_a_disconnected_chain_left_to_right(self):
        points = places(1, [1, 2, 8, 9], [(1, 2), (8, 9)])
        self.assertLess(points[8]["x"], points[9]["x"], "second component stays a vertical pair")

    def test_places_put_a_second_component_below_the_source_component(self):
        points = places(1, [1, 2, 8, 9], [(1, 2), (8, 9)])
        self.assertLess(points[1]["y"], points[8]["y"], "disconnected component shares the source row")

    def test_places_do_not_stack_isolated_names_on_one_point(self):
        points = places("α", ["α", "ω"], [])
        self.assertNotEqual((points["α"]["x"], points["α"]["y"]), (points["ω"]["x"], points["ω"]["y"]), "isolated names collide")
