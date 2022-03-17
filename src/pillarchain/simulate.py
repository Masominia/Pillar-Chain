"""Time integration with kicks, and the spikes that result."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from .model import Laser, Network, make_rhs, rest_state

RTOL, ATOL = 1e-9, 1e-12


@dataclass(frozen=True)
class Kick:
    """An instantaneous addition to the field of one site: `amplitude` at phase `phase` (degrees)."""

    site: int
    time: float
    amplitude: float
    phase: float = 0.0


@dataclass
class Result:
    sites: int
    duration: float
    spikes: list[list[tuple[float, float]]]  # per site: (time, peak intensity) of each spike
    segments: list = field(default_factory=list)  # dense solutions between kicks

    def arrival(self, site: int) -> float | None:
        s = self.spikes[site - 1]
        return s[0][0] if s else None

    def count(self, site: int) -> int:
        return len(self.spikes[site - 1])

    @property
    def total(self) -> int:
        return sum(len(s) for s in self.spikes)

    @property
    def last_spike(self) -> float | None:
        times = [t for s in self.spikes for t, _ in s]
        return max(times) if times else None

    def intensity(self, times: np.ndarray) -> np.ndarray:
        """Intensity of every site at the given times: an array of shape (sites, len(times))."""
        times = np.asarray(times, dtype=float)
        out = np.zeros((self.sites, len(times)))
        for t0, t1, sol in self.segments:
            mask = (times >= t0) & (times <= t1)
            if mask.any():
                y = sol(times[mask])
                out[:, mask] = y[2 * self.sites : 3 * self.sites] ** 2 + y[3 * self.sites :] ** 2
        return out


def _spikes_of_segment(sol, rhs, n: int, threshold: float) -> list[list[tuple[float, float]]]:
    """Intensity maxima above the threshold on one integrated segment, located on its dense solution."""
    t = sol.t
    y = sol.y
    re, im = y[2 * n : 3 * n], y[3 * n :]
    slopes = np.array([rhs(ti, y[:, k]) for k, ti in enumerate(t)]).T
    d_intensity = 2.0 * (re * slopes[2 * n : 3 * n] + im * slopes[3 * n :])
    intensity = re * re + im * im
    found: list[list[tuple[float, float]]] = [[] for _ in range(n)]
    for site in range(n):
        rising = d_intensity[site]
        for k in np.nonzero((rising[:-1] > 0) & (rising[1:] <= 0))[0]:
            if max(intensity[site, k], intensity[site, k + 1]) < 0.2 * threshold:
                continue

            def slope(tau, site=site):
                state = sol.sol(tau)
                d = rhs(tau, state)
                return state[2 * n + site] * d[2 * n + site] + state[3 * n + site] * d[3 * n + site]

            tau = brentq(slope, t[k], t[k + 1], xtol=1e-12 * max(1.0, t[k + 1]))
            state = sol.sol(tau)
            peak = float(state[2 * n + site] ** 2 + state[3 * n + site] ** 2)
            if peak >= threshold:
                found[site].append((float(tau), peak))
    return found


def simulate(network: Network, laser: Laser, kicks: list[Kick], duration: float, threshold: float = 5.0) -> Result:
    """Integrates from rest, applying the kicks at their times. A spike is an intensity maximum above `threshold`."""
    n = network.sites
    if n < 1:
        raise ValueError("the network has no sites")
    for kick in kicks:
        network._check(kick.site)
        if not 0.0 <= kick.time < duration:
            raise ValueError(f"the kick at time {kick.time:g} lies outside the run")
    rhs = make_rhs(network, laser)
    y = rest_state(network, laser)
    times = sorted({k.time for k in kicks} | {0.0, duration})
    result = Result(n, duration, [[] for _ in range(n)])
    for t0, t1 in zip(times[:-1], times[1:], strict=True):
        for kick in kicks:
            if kick.time == t0:
                angle = np.radians(kick.phase)
                y[2 * n + kick.site - 1] += kick.amplitude * np.cos(angle)
                y[3 * n + kick.site - 1] += kick.amplitude * np.sin(angle)
        sol = solve_ivp(rhs, (t0, t1), y, method="DOP853", rtol=RTOL, atol=ATOL, dense_output=True)
        if not sol.success:
            raise RuntimeError(f"integration failed: {sol.message}")
        for site, found in enumerate(_spikes_of_segment(sol, rhs, n, threshold)):
            result.spikes[site] += found
        result.segments.append((t0, t1, sol.sol))
        y = sol.y[:, -1].copy()
    return result
