"""Draw the figure of one case: traces for a single pillar, a raster of site against time otherwise.

python scripts/plot_case.py cases/ring_second_kick185.pil ring.png
"""

import sys

from pillarchain import plotting
from pillarchain.runner import run_file

if __name__ == "__main__":
    record, case, result = run_file(sys.argv[1])
    target = sys.argv[2] if len(sys.argv) > 2 else f"{record['case']}.png"
    plotting.case_figure(record, case, result, target)
    print(f"wrote {target}")
