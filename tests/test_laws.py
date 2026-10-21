"""Tests for reliability.laws factories."""

import random
import unittest

from reliability.laws import custom, exponential, normal, truncated_normal


class LawTests(unittest.TestCase):
    """Vertex lifetime draws used by Monte Carlo trials."""

    def test_exponential_draws_a_positive_time(self):
        sample = exponential(0.73)(random.Random(41))
        self.assertTrue(sample > 0.0, "exponential draw is not strictly positive")

    def test_truncated_normal_stays_above_the_floor(self):
        floor = 4.5
        sample = truncated_normal(3.0, 2.0, low=floor)(random.Random(8))
        self.assertTrue(sample >= floor, "truncated normal draw falls through the floor")

    def test_normal_uses_the_given_generator(self):
        first = normal(11.0, 2.5)(random.Random(14))
        second = normal(11.0, 2.5)(random.Random(14))
        self.assertEqual(first, second, "normal draw ignores the seeded generator")

    def test_custom_draws_the_written_expression(self):
        sample = custom("3.25 + 0.0 * rng.random()")(random.Random(2))
        self.assertEqual(sample, 3.25, "custom law ignores its expression")
