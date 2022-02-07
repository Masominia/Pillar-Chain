"""Simulates one network file and turns the result into plain data."""

from __future__ import annotations

from pathlib import Path

from .casefile import Case, load
from .expect import evaluate
from .simulate import Result, simulate


def run_case(case: Case) -> Result:
    return simulate(case.network, case.laser, case.kicks, case.duration, case.threshold)


def record_of(case: Case, result: Result) -> dict:
    laser = case.laser
    return {
        "title": case.title,
        "laser": {"A": laser.A, "B": laser.B, "a": laser.a, "gamma": laser.gamma, "alpha": laser.alpha},
        "sites": case.network.sites,
        "links": len(case.network.links),
        "duration": case.duration,
        "kicks": [{"site": k.site, "time": k.time, "amplitude": k.amplitude, "phase": k.phase} for k in case.kicks],
        "total": result.total,
        "last_spike": result.last_spike,
        "spikes": {
            str(site + 1): [[t, peak] for t, peak in found] for site, found in enumerate(result.spikes) if found
        },
    }


def run_file(path: Path | str) -> tuple[dict, Case, Result]:
    """Loads, simulates and checks one file. Raises ValueError for a file that cannot be read as a case."""
    case = load(path)
    result = run_case(case)
    record = record_of(case, result)
    record["case"] = Path(path).stem
    record["checks"] = [
        {"check": c.name, "status": "PASS" if c.passed else "FAIL", "detail": c.detail} for c in evaluate(case, result)
    ]
    return record, case, result


def render(record: dict) -> str:
    """A short text report of one record."""
    lines = [
        record["title"] or record.get("case", ""),
        f"  {record['sites']} sites, {record['links']} links, {len(record['kicks'])} kick(s), "
        f"{record['duration']:g} photon lifetimes: {record['total']} spike(s)",
    ]
    for site, found in list(record["spikes"].items())[:40]:
        times = ", ".join(f"{t:.2f}" for t, _ in found[:6]) + (", ..." if len(found) > 6 else "")
        lines.append(f"  site {site:>3}: {len(found)} spike(s) at {times}; first peak {found[0][1]:.2f}")
    if len(record["spikes"]) > 40:
        lines.append(f"  ... and {len(record['spikes']) - 40} more sites")
    for c in record["checks"]:
        lines.append(f"  {c['status']}  {c['check']}  ({c['detail']})")
    return "\n".join(lines)
