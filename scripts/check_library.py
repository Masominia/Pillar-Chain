"""Simulate every case of the library and print one line each. Exit status 1 if any expectation fails.

python scripts/check_library.py [directory]
"""

import sys
from pathlib import Path

from pillarchain import cases
from pillarchain.cases import ROOT
from pillarchain.runner import run_file

if __name__ == "__main__":
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "cases"
    failures = 0
    for path in cases.discover(directory):
        record, _, _ = run_file(path)
        bad = [c for c in record["checks"] if c["status"] != "PASS"]
        failures += len(bad)
        passed = len(record["checks"]) - len(bad)
        state = "ok  " if not bad else "FAIL"
        print(f"{state} {path.stem:<30} {record['total']:>4} spikes  {passed}/{len(record['checks'])}")
        for c in bad:
            print(f"       {c['check']}: {c['detail']}")
    sys.exit(1 if failures else 0)
