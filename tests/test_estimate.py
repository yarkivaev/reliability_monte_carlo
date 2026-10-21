"""Tests for reliability.estimate."""

import random
import statistics
import threading
import unittest

from reliability.estimate import mean_lifetime, path
from reliability.laws import exponential, normal, truncated_normal
from reliability.network import Network


def frozen(value):
    """Return a law that ignores the generator and yields value."""
    return lambda rng: value


class MeanTests(unittest.TestCase):
    """Monte Carlo mean and normal confidence interval."""

    def test_path_keeps_the_mean_of_the_first_prefix(self):
        samples = [1.25, 7.5, 0.3, 4.0, 9.75]
        self.assertEqual(path(samples, [2, 5], 0.9)[0]["mean"], statistics.fmean(samples[:2]), "path mean leaves the first prefix")

    def test_mean_lifetime_keeps_a_constant_lifetime(self):
        value = 12.75 + random.Random(19).random()
        product = Network(1, 2, {1: frozen(value), 2: frozen(value + 3.4)}, [(1, 2)])
        estimate = mean_lifetime(product, trials=24, seed=4, level=0.91)
        self.assertEqual(estimate.mean, value, "constant laws do not reproduce the folded lifetime")

    def test_mean_lifetime_collapses_the_interval_for_a_constant_law(self):
        value = 8.125
        product = Network(1, 1, {1: frozen(value)}, [])
        estimate = mean_lifetime(product, trials=16, seed=11, level=0.8)
        self.assertEqual((estimate.low, estimate.high), (value, value), "zero sample variance still opens an interval")

    def test_mean_lifetime_repeats_the_interval_for_one_seed(self):
        first = mean_lifetime(Network(1, 1, {1: exponential(0.31)}, []), trials=200, seed=91, level=0.9)
        second = mean_lifetime(Network(1, 1, {1: exponential(0.31)}, []), trials=200, seed=91, level=0.9)
        self.assertEqual(
            (first.mean, first.error, first.low, first.high),
            (second.mean, second.error, second.low, second.high),
            "one seed yields two different intervals",
        )

    def test_mean_lifetime_covers_the_exponential_mean(self):
        rate = 0.37
        covered = False
        for attempt in range(5):
            estimate = mean_lifetime(
                Network(1, 1, {1: exponential(rate)}, []),
                trials=8000,
                seed=17 + attempt,
                level=0.95,
            )
            covered = estimate.low <= 1.0 / rate <= estimate.high
            if covered:
                break
        self.assertTrue(covered, "interval misses the exponential mean")

    def test_mean_lifetime_accepts_a_lambda_and_a_truncated_normal(self):
        product = Network(
            1,
            2,
            {
                1: lambda rng: rng.gauss(9.0, 0.01),
                2: truncated_normal(9.0, 0.01, low=0.0),
            },
            [(1, 2)],
        )
        estimate = mean_lifetime(product, trials=80, seed=5, level=0.95)
        self.assertTrue(8.5 <= estimate.mean <= 9.5, "mixed laws drift away from the common center")

    def test_mean_lifetime_accepts_a_normal_law(self):
        product = Network(1, 1, {1: normal(20.0, 0.05)}, [])
        estimate = mean_lifetime(product, trials=200, seed=2, level=0.99)
        self.assertTrue(19.5 <= estimate.mean <= 20.5, "normal law drifts away from its center")

    def test_mean_lifetime_rejects_a_single_trial(self):
        self.assertRaises(ValueError, mean_lifetime, Network(1, 1, {1: frozen(1.0)}, []), 1, 0, 0.95)

    def test_mean_lifetime_repeats_when_two_threads_share_a_seed(self):
        boxes = [None, None]
        def run(index):
            boxes[index] = mean_lifetime(Network(1, 1, {1: exponential(0.44)}, []), trials=120, seed=63, level=0.88)
        first = threading.Thread(target=run, args=(0,))
        second = threading.Thread(target=run, args=(1,))
        first.start()
        second.start()
        first.join(timeout=5.0)
        second.join(timeout=5.0)
        self.assertEqual(boxes[0].mean, boxes[1].mean, "two threads with one seed diverge")
