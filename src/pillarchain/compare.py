"""Compares a simulation with the independent integration of the same network."""

from __future__ import annotations

import numpy as np

from . import reference
from .casefile import Case
from .simulate import Result

TOLERANCES = {"spike time": 5e-3, "spike peak": 2e-4, "dark intensity": 1e-6}


def compare(case: Case, result: Result) -> dict:
    """Integrates the case again by the reference route. Returns the disagreements and the largest differences.

    Spike times are absolute differences in photon lifetimes, peaks relative. The dark intensity is compared on
    a logarithmic scale at times before the first spike, where it spans many decades.
    """
    ref = reference.simulate(case)
    diff: dict[str, float] = {}
    outside: list[str] = []
    for site, (mine, theirs) in enumerate(zip(result.spikes, ref["spikes"], strict=True), start=1):
        if len(mine) != len(theirs):
            outside.append(f"site {site}: {len(mine)} spikes against {len(theirs)}")
            continue
        for (t, peak), (t_ref, peak_ref) in zip(mine, theirs, strict=True):
            diff["spike time"] = max(diff.get("spike time", 0.0), abs(t - t_ref))
            diff["spike peak"] = max(diff.get("spike peak", 0.0), abs(peak / peak_ref - 1))
    first = min((s[0][0] for s in result.spikes if s), default=case.duration)
    start = min((k.time for k in case.kicks), default=0.0)
    if first - start > 2.0:
        times = np.linspace(start + 0.2 * (first - start), start + 0.7 * (first - start), 7)
        mine, theirs = result.intensity(times), ref["intensity"](times)
        seen = theirs > 1e-12
        if seen.any():
            diff["dark intensity"] = float(np.abs(np.log(mine[seen] / theirs[seen])).max())
    outside += [f"{name} differs by {value:.2e}" for name, value in diff.items() if value > TOLERANCES[name]]
    return {"outside": outside, "differences": diff}
