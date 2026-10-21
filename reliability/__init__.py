"""Monte Carlo mean lifetime of a directed reliability network.

Vertices fail independently. Edges only route work. Product lifetime is the
longest time a source-sink path stays alive.

Usage:
    product = Network(1, 7, {1: exponential(0.02), 7: exponential(0.01)}, [(1, 7)])
    estimate = mean_lifetime(product, trials=10_000, seed=7)
"""

from reliability.estimate import Estimate, draws, mean_lifetime
from reliability.laws import custom, exponential, normal, truncated_normal
from reliability.network import Network
from reliability.scheme import scheme

__all__ = [
    "Estimate",
    "Network",
    "custom",
    "draws",
    "exponential",
    "mean_lifetime",
    "normal",
    "scheme",
    "truncated_normal",
]
