"""Find the smallest coupling that carries a pulse along a chain, by bisection.

python scripts/critical.py [--pump 6.5] [--kick 2] [--alpha 2] [--gamma 0.01]
"""

import argparse

from pillarchain.model import Laser
from pillarchain.studies import critical_coupling

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pump", type=float, default=6.5)
    ap.add_argument("--kick", type=float, default=2.0)
    ap.add_argument("--alpha", type=float, default=2.0)
    ap.add_argument("--gamma", type=float, default=0.01)
    args = ap.parse_args()
    laser = Laser(A=args.pump, alpha=args.alpha, gamma=args.gamma)
    try:
        print(f"critical coupling: {critical_coupling(laser, kick=args.kick):.5f} per photon lifetime")
    except ValueError as err:
        raise SystemExit(f"critical.py: {err}") from None
