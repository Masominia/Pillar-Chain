"""Simulates the whole library of networks, checks it and writes the report."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import cases, plotting, studies
from .cases import ROOT
from .compare import compare
from .model import Laser
from .report import md_table
from .runner import run_file

STEP_CASE = "sites 3\npath 1 3 kappa=0.06\nkick 1 amplitude=2\nrun 60\n"
ONCE = (
    "collision_odd",
    "collision_even",
    "collision_offset",
    "collision_three",
    "ring_single_n12",
    "ring_single_n13",
    "grid_two_corners",
    "grid_corner",
)


def _check(area, check, ok, detail):
    return {"area": area, "check": check, "status": "PASS" if ok else "FAIL", "detail": detail}


def run(cfg_path=None, out=None, fast: bool = False) -> dict:
    cfg = yaml.safe_load(open(cfg_path or ROOT / "configs" / "default.yaml"))
    out = Path(out) if out else ROOT / "reports"
    (out / "figures" / "cases").mkdir(parents=True, exist_ok=True)
    paths = cases.discover(ROOT / cfg["cases_dir"])
    if fast:
        keep = tuple(cfg["fast_families"])
        paths = [p for i, p in enumerate(paths) if i % cfg["fast_every"] == 0 or p.stem.startswith(keep)]
    pick = lambda key: cfg[f"fast_{key}" if fast else key]  # noqa: E731

    checks, rows, worst, records, shown = [], [], {}, {}, {}
    wanted = {case: title for title, case in cfg["overview"].items()}
    for path in paths:
        record, case, result = run_file(path)
        record["notes"] = cases.notes(path)
        family = cases.family_of(path.stem, cfg["families"])
        cmp = compare(case, result)
        record["against_reference"] = cmp["differences"]
        for name, diff in cmp["differences"].items():
            worst[name] = max(worst.get(name, 0.0), diff)
        checks.append(
            _check(
                "independent integration",
                f"{path.stem}: the same spikes, at the same times and heights, from the reference",
                not cmp["outside"],
                "; ".join(cmp["outside"]) or "agree",
            )
        )
        cases.write_record(record, out / "cases")
        plotting.case_figure(record, case, result, out / "figures" / "cases" / f"{path.stem}.png")
        for c in record["checks"]:
            checks.append(
                {"area": family, "check": f"{path.stem}: {c['check']}", "status": c["status"], "detail": c["detail"]}
            )
        records[path.stem] = record
        if path.stem in wanted:
            shown[wanted[path.stem]] = (case, result)
        rows.append(
            {
                "case": path.stem,
                "family": family,
                "sites": record["sites"],
                "links": record["links"],
                "kicks": len(record["kicks"]),
                "spikes": record["total"],
                "last spike": record["last_spike"] if record["last_spike"] is not None else np.nan,
                "checks": len(record["checks"]),
                "passed": sum(c["status"] == "PASS" for c in record["checks"]),
            }
        )

    table = pd.DataFrame(rows)
    fam = table.groupby("family", sort=False).agg(
        cases=("case", "size"),
        sites=("sites", "sum"),
        spikes=("spikes", "sum"),
        checks=("checks", "sum"),
        passed=("passed", "sum"),
    )
    laser = Laser(**cfg["laser"])
    lines, study = [], {}

    speed = studies.speed(laser, pick("speed_couplings"))
    delays = speed["delay per site"].to_numpy()
    checks.append(
        _check(
            "speed",
            "the delay per site shortens steadily as the coupling grows",
            bool(np.isfinite(delays).all() and (np.diff(delays) < 0).all()),
            f"{delays[0]:.1f} photon lifetimes at {speed['coupling'].iloc[0]:g}, {delays[-1]:.1f} at {speed['coupling'].iloc[-1]:g}",
        )
    )
    critical = studies.critical_coupling(laser)
    checks.append(
        _check(
            "speed",
            "the critical coupling found by bisection lies between the failing and the passing chain of the library",
            0.040 < critical < 0.042,
            f"{critical:.5f}",
        )
    )
    lines += [
        "### Pulse speed against coupling (chain of 12, measured between sites 4 and 8)",
        "",
        f"Critical coupling for a kick of amplitude 2, by bisection: {critical:.5f}.",
        "",
        md_table(speed, 4, index=False),
        "",
    ]
    study["speed"] = speed.to_dict("records")
    study["critical_coupling"] = critical

    pumps = studies.critical_against_pump(laser, pick("critical_pumps"))
    checks.append(
        _check(
            "critical coupling",
            "a pillar pumped closer to threshold needs less coupling",
            bool((np.diff(pumps["critical coupling"]) < 0).all()),
            f"{pumps['critical coupling'].iloc[0]:.4f} at A = {pumps['pump'].iloc[0]:g}, {pumps['critical coupling'].iloc[-1]:.4f} at {pumps['pump'].iloc[-1]:g}",
        )
    )
    kicks = studies.critical_against_kick(laser, pick("critical_kicks"))
    spread = float(kicks["critical coupling"].max() - kicks["critical coupling"].min())
    lines += [
        "### Critical coupling against the pump (kick of amplitude 2.5)",
        "",
        md_table(pumps, 4, index=False),
        "",
        "### Critical coupling against the launching kick",
        "",
        f"The threshold depends on how the pulse is launched: it moves by {spread:.4f} over these kicks. It is not monotonic in the kick.",
        "",
        md_table(kicks, 4, index=False),
        "",
    ]
    study["critical_against_pump"] = pumps.to_dict("records")
    study["critical_against_kick"] = kicks.to_dict("records")

    refr = studies.refractory(laser, pick("refractory_kicks"))
    checks.append(
        _check(
            "refractory time",
            "a pillar that has just fired needs about a carrier lifetime before it can fire again",
            bool(refr["refractory time"].between(0.5 / laser.gamma, 2.5 / laser.gamma).all()),
            f"{refr['refractory time'].min():.0f} to {refr['refractory time'].max():.0f} photon lifetimes, carrier lifetime {1 / laser.gamma:.0f}",
        )
    )
    checks.append(
        _check(
            "refractory time",
            "the weakest kick has to wait longest",
            bool(refr["refractory time"].idxmax() == refr["kick"].idxmin()),
            f"{refr['refractory time'].iloc[0]:.0f} photon lifetimes for a kick of {refr['kick'].iloc[0]:g}",
        )
    )
    lines += [
        "### Refractory time of one pillar against the kick",
        "",
        "Shortest delay after which a second kick of the same amplitude fires the pillar again, by bisection between 20 and 600.",
        "",
        md_table(refr, 3, index=False),
        "",
    ]
    study["refractory"] = refr.to_dict("records")

    once = [n for n in ONCE if n in records]
    bad = [
        n
        for n in once
        if any(len(s) != 1 for s in records[n]["spikes"].values()) or len(records[n]["spikes"]) != records[n]["sites"]
    ]
    checks.append(
        _check(
            "annihilation",
            "when pulses meet they annihilate: every site fires exactly once, nothing passes through",
            not bad and bool(once),
            f"{len(once)} cases" + (f", not {bad}" if bad else ""),
        )
    )

    delay60 = float(studies.speed(laser, [0.06])["delay per site"].iloc[0])
    circ = studies.circulation(laser, pick("ring_sizes"), 0.06, cfg["ring_second_kick"], delay60)
    slow = circ["over open chain"].to_numpy()
    checks.append(
        _check(
            "rings",
            "a pulse held in a ring runs into its own wake: it is slower than in an open chain, more so in a shorter ring",
            bool(np.isfinite(slow).all() and (slow > 1).all() and (np.diff(slow) < 0).all()),
            ", ".join(
                f"{int(r['sites'])} sites: {r['round trip']:.1f} per round trip, {r['over open chain']:.3f} of the open-chain delay per site"
                for _, r in circ.iterrows()
            ),
        )
    )
    checks.append(
        _check(
            "rings",
            "the round trip has settled by the end of the run",
            bool(circ["settling"].max() < 1e-3),
            f"last two round trips differ by at most {circ['settling'].max():.1e}",
        )
    )
    lines += [
        "### Pulses held in rings",
        "",
        f"Coupling 0.06, second kick on the last site at t = {cfg['ring_second_kick']:g}. Delay per site of an open chain at the same coupling: {delay60:.3f}.",
        "",
        md_table(circ, 4, index=False),
        "",
    ]
    study["circulation"] = circ.to_dict("records")

    gates = studies.gates(records)
    if len(gates):
        g = gates.set_index("case")["output"].to_dict()
        want = {
            "junction_and_first": "no",
            "junction_and_second": "no",
            "junction_and_both": "yes",
            "junction_and_antiphase": "no",
            "junction_or_one": "yes",
            "junction_or_both": "yes",
            "junction_xor": "no",
        }
        present = {k: v for k, v in want.items() if k in g}
        checks.append(
            _check(
                "junctions",
                "the weak junction answers only to two pulses in phase, the strong one to one pulse or two in phase, neither to two in antiphase",
                all(g[k] == v for k, v in present.items()) and bool(present),
                f"{len(present)} cases",
            )
        )
        lines += [
            "### What comes out of the junctions",
            "",
            "Phase and lag of the second input relative to the first; output read at the end of the output arm.",
            "",
            md_table(gates, 2, index=False),
            "",
        ]
        study["gates"] = json.loads(gates.to_json(orient="records"))

    sym = studies.symmetry(laser)
    checks.append(
        _check(
            "symmetry",
            "a common phase on every kick changes nothing",
            sym["phase"] < 1e-5,
            f"spike times move by {sym['phase']:.1e}",
        )
    )
    checks.append(
        _check(
            "symmetry",
            "the mirror image of a chain gives the mirror image of the spikes",
            sym["mirror"] < 1e-5,
            f"spike times differ by {sym['mirror']:.1e}",
        )
    )
    conv = studies.step_convergence(STEP_CASE)
    orders = conv["order"].dropna().to_numpy()
    checks.append(
        _check(
            "integration",
            "a fixed-step fourth-order integration converges to the adaptive one at fourth order",
            bool(((orders > 3.5) & (orders < 4.5)).all()),
            f"orders {', '.join(f'{o:.2f}' for o in orders)}, difference {conv['difference'].iloc[-1]:.1e} at step {conv['step'].iloc[-1]:g}",
        )
    )
    lines += [
        "### Fixed-step integration against the adaptive solver (three sites, one pulse)",
        "",
        md_table(conv, 4, index=False),
        "",
    ]
    study["symmetry"] = sym
    study["step_convergence"] = json.loads(conv.to_json(orient="records"))

    plotting.overview(speed, critical, pumps, shown, out / "figures" / "overview.png")

    val = pd.DataFrame(checks)
    counts = val["status"].value_counts().to_dict()
    agreement = pd.DataFrame({"largest difference over the library": worst}).rename_axis("quantity")
    report = [
        "# PillarChain report",
        "",
        f"{len(table)} networks, {int(table['sites'].sum())} pillars, {int(table['spikes'].sum())} spikes, {len(val)} checks: {counts.get('PASS', 0)} PASS, {counts.get('FAIL', 0)} FAIL.",
        "",
        "Every network is a text file in `cases/`. Its expectations come from an independent integration or a closed form, stated in the comments at the top of the file.",
        "Per-case results are in `reports/cases/`, figures in `reports/figures/cases/`. Times are in photon lifetimes.",
        "",
        "## Families",
        "",
        md_table(fam, 0),
        "",
        "## Agreement with the independent integration",
        "",
        "Spike times are absolute differences in photon lifetimes, peaks relative, dark intensities differences of the logarithm before the first spike.",
        "",
        md_table(agreement, 10),
        "",
        "## Studies",
        "",
        *lines,
        "## All networks",
        "",
        md_table(table.drop(columns=["family"]), 3, index=False),
        "",
    ]
    (out / "report.md").write_text("\n".join(report))
    (out / "validation.md").write_text("# Validation checks\n\n" + md_table(val, index=False) + "\n")
    metrics = {
        "cases": len(table),
        "pillars": int(table["sites"].sum()),
        "spikes": int(table["spikes"].sum()),
        "families": fam.to_dict("index"),
        "largest_differences": worst,
        "studies": study,
        "cases_table": json.loads(table.set_index("case").to_json(orient="index")),
        "checks": checks,
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=float))
    return metrics
