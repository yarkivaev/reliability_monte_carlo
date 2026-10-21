"""Run Monte Carlo on the seven-element figure from the notes."""

from reliability import Network, exponential, mean_lifetime, truncated_normal


def figure(laws):
    """Build the source-sink graph drawn in the assignment."""
    return Network(
        1,
        7,
        laws,
        [(1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 6), (5, 7), (6, 7)],
    )


def report(title, estimate):
    """Print the mean, standard error and default 95 percent interval."""
    print(title)
    print(f"  mean {estimate.mean:.4f}")
    print(f"  error {estimate.error:.4f}")
    print(f"  interval ({estimate.low:.4f}, {estimate.high:.4f})")


def main():
    """Estimate lifetime for an exponential figure and a mixed-wear figure."""
    rates = figure({node: exponential(0.02 * node) for node in range(1, 8)})
    report("exponential figure", mean_lifetime(rates, trials=20_000, seed=7, level=0.95))
    mixed = figure(
        {
            1: exponential(0.02),
            2: lambda rng: rng.gauss(120.0, 15.0),
            3: truncated_normal(100.0, 12.0, low=0.0),
            4: truncated_normal(80.0, 10.0, low=0.0),
            5: exponential(0.01),
            6: lambda rng: max(0.0, rng.normalvariate(90.0, 8.0)),
            7: exponential(0.015),
        }
    )
    report("mixed wear figure", mean_lifetime(mixed, trials=20_000, seed=7, level=0.95))


if __name__ == "__main__":
    main()
