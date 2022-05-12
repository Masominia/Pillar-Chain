"""Command line entry point.

python -m pillarchain check <file>             simulate one network; exit status 1 if a check fails
python -m pillarchain run [--fast] [--out DIR]   simulate the library and write the report
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    ap = argparse.ArgumentParser(prog="pillarchain")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="simulate one network file")
    c.add_argument("file")
    r = sub.add_parser("run", help="simulate the library and write the report")
    r.add_argument("--fast", action="store_true", help="a subset, for continuous integration")
    r.add_argument("--out", default=None, help="output directory (default: reports/)")
    args = ap.parse_args()
    if args.cmd == "check":
        from .runner import render, run_file

        try:
            record, _, _ = run_file(args.file)
        except (OSError, ValueError) as err:
            print(f"pillarchain: {err}", file=sys.stderr)
            sys.exit(2)
        print(render(record))
        sys.exit(1 if any(k["status"] == "FAIL" for k in record["checks"]) else 0)
    from .pipeline import run

    m = run(out=args.out, fast=args.fast)
    fails = sum(k["status"] == "FAIL" for k in m["checks"])
    print(f"Reports written ({len(m['checks'])} checks, {fails} FAIL)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
