"""Tests for reliability.network."""

import unittest

from reliability.network import Network


class NetworkTests(unittest.TestCase):
    """Graph wrapper that stores the folded lifetime formula."""

    def test_network_lifetime_follows_the_folded_formula(self):
        product = Network("вход", "выход", {"вход": None, "выход": None}, [("вход", "выход")])
        times = {"вход": 6.4, "выход": 2.8}
        self.assertEqual(product.lifetime(times), 2.8, "network lifetime ignores the shorter vertex")
