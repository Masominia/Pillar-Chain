"""Studies that go beyond single cases: speed, critical coupling, refractory time, circulation, convergence."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import reference
from .casefile import parse
from .model import Laser, Network
from .simulate import Kick, simulate


def chain(sites: int, kappa: float) -> Network:
    net = Network()
    net.add_sites(sites)
    net.path(1, sites, kappa)
    return net


def propagates(laser: Laser, kappa: float, sites: int = 6, kick: float = 2.0, duration: float = 2500.0) -> bool:
    """Whether a pulse launched at one end of a chain reaches the other end."""
    result = simulate(chain(sites, kappa), laser, [Kick(1, 0.0, kick)], duration)
    return result.count(sites) > 0


def critical_coupling(laser: Laser, low: float = 0.01, high: float = 0.12, tolerance: float = 2e-5, **kwargs) -> float:
    """The smallest coupling that carries a pulse along a chain, by bisection. Raises if the bracket is wrong."""
    if propagates(laser, low, **kwargs) or not propagates(laser, high, **kwargs):
        raise ValueError(f"no critical coupling between {low:g} and {high:g}")
    while high - low > tolerance:
        mid = 0.5 * (low + high)
        low, high = (low, mid) if propagates(laser, mid, **kwargs) else (mid, high)
    return 0.5 * (low + high)


def speed(laser: Laser, kappas, sites: int = 12) -> pd.DataFrame:
    """Delay per site and pulse height in the middle of a chain against the coupling."""
    rows = []
    for kappa in kappas:
        r = simulate(chain(sites, kappa), laser, [Kick(1, 0.0, 2.0)], 2500.0)
        if r.count(sites) != 1:
            rows.append({"coupling": kappa, "delay per site": np.nan, "peak": np.nan, "delay times coupling": np.nan})
            continue
        a, b = sites // 3, 2 * sites // 3
        delay = (r.arrival(b) - r.arrival(a)) / (b - a)
        rows.append(
            {
                "coupling": kappa,
                "delay per site": delay,
                "peak": r.spikes[sites // 2 - 1][0][1],
                "delay times coupling": delay * kappa,
            }
        )
    return pd.DataFrame(rows)


def critical_against_pump(laser: Laser, pumps) -> pd.DataFrame:
    """Critical coupling against the pump: an easier pillar to excite needs less light from its neighbour."""
    rows = []
    for pump in pumps:
        la = Laser(A=pump, B=laser.B, a=laser.a, gamma=laser.gamma, alpha=laser.alpha)
        rows.append(
            {
                "pump": pump,
                "distance below threshold": 1 + la.B - pump,
                "critical coupling": critical_coupling(la, kick=2.5, tolerance=1e-4),
            }
        )
    return pd.DataFrame(rows)


def critical_against_kick(laser: Laser, kicks) -> pd.DataFrame:
    """Critical coupling against the amplitude of the launching kick: near the threshold the launch matters."""
    return pd.DataFrame(
        [{"kick": k, "critical coupling": critical_coupling(laser, kick=k, tolerance=1e-4)} for k in kicks]
    )


def symmetry(laser: Laser, sites: int = 9, kappa: float = 0.06) -> dict:
    """Two exact symmetries of the equations: a common phase on every kick, and the mirror image of a chain."""
    net = chain(sites, kappa)
    base = simulate(net, laser, [Kick(1, 0.0, 2.0), Kick(sites, 30.0, 2.0)], 600.0)
    turned = simulate(net, laser, [Kick(1, 0.0, 2.0, 37.0), Kick(sites, 30.0, 2.0, 37.0)], 600.0)
    mirror = simulate(net, laser, [Kick(sites, 0.0, 2.0), Kick(1, 30.0, 2.0)], 600.0)

    def gap(a, b):
        if [len(s) for s in a] != [len(s) for s in b]:
            return float("inf")
        return max(
            (abs(x[0] - y[0]) for s, t in zip(a, b, strict=True) for x, y in zip(s, t, strict=True)), default=0.0
        )

    return {"phase": gap(base.spikes, turned.spikes), "mirror": gap(base.spikes, mirror.spikes[::-1])}


def refractory_time(laser: Laser, kick: float, low: float = 20.0, high: float = 600.0, tolerance: float = 0.5) -> float:
    """Shortest delay after which a second kick of the same amplitude fires a single pillar again."""

    def fires(delay: float) -> bool:
        net = Network()
        net.add_sites(1)
        return simulate(net, laser, [Kick(1, 0.0, kick), Kick(1, delay, kick)], delay + 500.0).count(1) == 2

    if fires(low) or not fires(high):
        raise ValueError("refractory time outside the bracket")
    while high - low > tolerance:
        mid = 0.5 * (low + high)
        low, high = (low, mid) if fires(mid) else (mid, high)
    return 0.5 * (low + high)


def refractory(laser: Laser, kicks) -> pd.DataFrame:
    return pd.DataFrame([{"kick": k, "refractory time": refractory_time(laser, k)} for k in kicks])


def ring(sites: int, kappa: float) -> Network:
    net = chain(sites, kappa)
    net.link(sites, 1, kappa)
    return net


def circulation(
    laser: Laser, sizes, kappa: float, second: float, delay: float, duration: float = 5000.0
) -> pd.DataFrame:
    """Round-trip time of a pulse held in a ring, against the number of sites times the delay of an open chain.

    The pulse is left by a kick on site 1 and a second one on the last site at time `second`. The round trip is
    the last interval between spikes of site 1; `settling` is how much it still changed over the last round trip.
    """
    rows = []
    for sites in sizes:
        r = simulate(ring(sites, kappa), laser, [Kick(1, 0.0, 2.0), Kick(sites, second, 2.0)], duration)
        times = [t for t, _ in r.spikes[0]]
        if len(times) < 5:
            rows.append({"sites": sites, "round trips": max(len(times) - 1, 0)})
            continue
        gaps = np.diff(times)
        rows.append(
            {
                "sites": sites,
                "round trips": len(gaps),
                "round trip": gaps[-1],
                "settling": abs(gaps[-1] - gaps[-2]),
                "per site": gaps[-1] / sites,
                "over open chain": gaps[-1] / sites / delay,
            }
        )
    return pd.DataFrame(rows)


def gates(records: dict[str, dict], output: str = "16") -> pd.DataFrame:
    """What comes out of the junction cases: one row per case."""
    rows = []
    for name, rec in records.items():
        if not name.startswith("junction_") or name == "junction_fanout":
            continue
        kicks = {k["site"]: k for k in rec["kicks"]}
        first, second = kicks.get(1), kicks.get(6)
        out = rec["spikes"].get(output)
        rows.append(
            {
                "case": name,
                "input 1": "yes" if first else "no",
                "input 2": "yes" if second else "no",
                "phase": second["phase"] - first["phase"] if first and second else np.nan,
                "lag": second["time"] - first["time"] if first and second else np.nan,
                "output": "yes" if out else "no",
                "at": out[0][0] if out else np.nan,
            }
        )
    return pd.DataFrame(rows)


def step_convergence(text: str, steps=(0.2, 0.1, 0.05)) -> pd.DataFrame:
    """Fixed-step Runge-Kutta against the adaptive solver: the difference must fall sixteen-fold per halving."""
    case = parse(text)
    from .runner import run_case

    result = run_case(case)
    final = result.segments[-1][2](case.duration)
    n = case.network.sites
    rows = []
    for step in steps:
        y = reference.rk4(case, step)
        rows.append({"step": step, "difference": float(np.abs(y - final).max() / np.abs(final[: 2 * n]).max())})
    t = pd.DataFrame(rows)
    t["order"] = np.log2(t["difference"].shift(1) / t["difference"])
    return t
