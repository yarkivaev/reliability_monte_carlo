"""Monte Carlo mean of product lifetime.

Usage:
    mean_lifetime(Network(1, 1, {1: exponential(1.0)}, []), trials=200, seed=3)
"""

import math
import random
import statistics


class Estimate:
    """Sample mean of product lifetime with a normal confidence interval.

    Usage:
        Estimate(4.0, 0.1, 3.8, 4.2).mean
    """

    def __init__(self, mean, error, low, high):
        self.mean = mean
        self.error = error
        self.low = low
        self.high = high


def scan(product, trials, seed):
    """Yield independent product lifetime samples.

    Usage:
        list(scan(Network(1, 1, {1: exponential(1.0)}, []), 200, 3))
    """
    rng = random.Random(seed)
    for _ in range(trials):
        times = {node: law(rng) for node, law in product.nodes.items()}
        yield product.lifetime(times)


def draws(product, trials, seed):
    """Return independent product lifetime samples.

    Usage:
        draws(Network(1, 1, {1: exponential(1.0)}, []), trials=200, seed=3)
    """
    return list(scan(product, trials, seed))


def summarize(samples, level=0.95):
    """Return the normal interval of a lifetime sample.

    Usage:
        summarize([1.0, 2.0, 3.0], level=0.95)
    """
    if len(samples) < 2:
        raise ValueError(f"sample size {len(samples)} is below 2 so the sample variance does not exist")
    center = statistics.fmean(samples)
    spread = statistics.variance(samples)
    error = math.sqrt(spread / len(samples))
    quantile = statistics.NormalDist().inv_cdf(0.5 + level / 2.0)
    return Estimate(center, error, center - quantile * error, center + quantile * error)


def path(samples, stops, level):
    """Return prefix estimates at each stop.

    Usage:
        path([1.0, 2.0, 3.0, 4.0], [2, 4], 0.95)
    """
    rows = []
    for stop in stops:
        estimate = summarize(samples[:stop], level)
        rows.append({
            "trials": stop,
            "mean": estimate.mean,
            "se": estimate.error,
            "low": estimate.low,
            "high": estimate.high,
        })
    return rows


def mean_lifetime(product, trials, seed, level=0.95):
    """Estimate expected product lifetime and a normal confidence interval.

    Usage:
        mean_lifetime(Network(1, 1, {1: exponential(1.0)}, []), trials=200, seed=3)
    """
    return summarize(draws(product, trials, seed), level)
