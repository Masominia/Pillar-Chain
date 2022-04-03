"""Kick one end of a chain and print when each pillar fires.

python scripts/chain.py --sites 10 --kappa 0.06 [--kick 2] [--pump 6.5] [--alpha 2]
"""

import argparse

from pillarchain.model import Laser
from pillarchain.simulate import Kick, simulate
from pillarchain.studies import chain

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", type=int, default=10)
    ap.add_argument("--kappa", type=float, default=0.06)
    ap.add_argument("--kick", type=float, default=2.0)
    ap.add_argument("--pump", type=float, default=6.5)
    ap.add_argument("--alpha", type=float, default=2.0)
    ap.add_argument("--duration", type=float, default=2500.0)
    args = ap.parse_args()
    result = simulate(
        chain(args.sites, args.kappa), Laser(A=args.pump, alpha=args.alpha), [Kick(1, 0.0, args.kick)], args.duration
    )
    previous = None
    for site in range(1, args.sites + 1):
        if not result.count(site):
            print(f"site {site:>3}: silent")
            continue
        t, peak = result.spikes[site - 1][0]
        step = "" if previous is None else f"  (+{t - previous:.2f})"
        print(f"site {site:>3}: {result.count(site)} spike(s), first at {t:9.3f}, peak {peak:.2f}{step}")
        previous = t
