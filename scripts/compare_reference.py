"""Integrate one case again by the independent route and print the differences.

python scripts/compare_reference.py cases/collision_odd.pil
"""

import sys

from pillarchain.compare import TOLERANCES, compare
from pillarchain.runner import run_file

if __name__ == "__main__":
    record, case, result = run_file(sys.argv[1])
    out = compare(case, result)
    for name, value in out["differences"].items():
        print(f"{name:<16} {value:.3e}   (tolerance {TOLERANCES[name]:.0e})")
    for line in out["outside"]:
        print("OUTSIDE:", line)
    sys.exit(1 if out["outside"] else 0)
