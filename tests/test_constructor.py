"""Tests for examples.constructor handlers."""

import unittest

from examples.constructor import figure, grow, layout, run, walk
from reliability.laws import custom


class ConstructorTests(unittest.TestCase):
    """JSON fold and Monte Carlo used by the constructor page."""

    def test_layout_returns_the_figure_layers(self):
        payload = layout(figure())
        self.assertEqual(payload["layers"], [[1], [2, 3, 4], [5, 6], [7]], "constructor layout misses the figure columns")

    def test_layout_rejects_a_cycle(self):
        spec = {
            "source": 1,
            "sink": 2,
            "nodes": [{"name": 1, "law": "constant", "value": 1.0}, {"name": 2, "law": "constant", "value": 1.0}],
            "edges": [(1, 2), (2, 1)],
        }
        self.assertRaises(ValueError, layout, spec)

    def test_run_keeps_a_constant_custom_law(self):
        spec = {
            "source": 1,
            "sink": 1,
            "nodes": [{"name": 1, "law": "custom", "source": "4.5 + 0.0 * rng.random()"}],
            "edges": [],
            "trials": 20,
            "seed": 3,
            "level": 0.9,
        }
        payload = run(spec)
        self.assertEqual(payload["mean"], 4.5, "custom constant law does not stay at 4.5")

    def test_custom_law_rejects_open(self):
        self.assertRaises(ValueError, custom, "open('x')")

    def test_walk_ends_with_the_asked_trial_count(self):
        spec = {
            "source": 1,
            "sink": 1,
            "nodes": [{"name": 1, "law": "constant", "value": 3.25}],
            "edges": [],
            "trials": 20,
            "seed": 5,
            "level": 0.9,
            "bins": 4,
        }
        self.assertEqual(list(walk(spec))[-1]["done"], 20, "stream ends before the last trial")

    def test_grow_ends_on_the_asked_end(self):
        spec = {
            "source": 1,
            "sink": 1,
            "nodes": [{"name": 1, "law": "constant", "value": 3.25}],
            "edges": [],
            "start": 2,
            "end": 20,
            "stops": 4,
            "spacing": "linear",
            "seed": 5,
            "level": 0.9,
        }
        self.assertEqual(list(grow(spec))[-1]["points"][-1]["trials"], 20, "growth path misses the last trial")

    def test_grow_keeps_the_asked_stop_count(self):
        spec = {
            "source": 1,
            "sink": 1,
            "nodes": [{"name": 1, "law": "exponential", "rate": 0.2}],
            "edges": [],
            "start": 2,
            "end": 16,
            "stops": 5,
            "spacing": "geometric",
            "seed": 11,
            "level": 0.9,
        }
        self.assertEqual(len(list(grow(spec))[-1]["points"]), 5, "growth path drops a stop")

    def test_run_keeps_the_asked_bin_count(self):
        spec = {
            "source": 1,
            "sink": 1,
            "nodes": [{"name": 1, "law": "exponential", "rate": 0.13}],
            "edges": [],
            "trials": 40,
            "seed": 11,
            "level": 0.9,
            "bins": 5,
        }
        payload = run(spec)
        self.assertEqual(len(payload["bins"]), 5, "constructor ignores the asked bin count")

    def test_run_collapses_the_interval_for_a_constant(self):
        spec = {
            "source": "вход",
            "sink": "вход",
            "nodes": [{"name": "вход", "law": "constant", "value": 8.0}],
            "edges": [],
            "trials": 12,
            "seed": 2,
            "level": 0.8,
        }
        payload = run(spec)
        self.assertEqual((payload["low"], payload["high"], payload["se"]), (8.0, 8.0, 0.0), "constant constructor run still opens an interval")
