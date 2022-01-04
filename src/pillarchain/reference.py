"""An independent simulation of every network, and closed forms for the dark, linear regime.

The equations are written again in complex arithmetic, integrated with LSODA (the package uses an explicit
Runge-Kutta method of order 8), and spikes are read from a fine sampling of the dense solution with a parabola
through each maximum. A fixed-step Runge-Kutta integrator of order 4 is provided for a third opinion on short runs.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .casefile import Case


def _setup(case: Case):
    n = case.network.sites
    coupling = np.zeros((n, n))
    for (i, j), kappa in case.network.links.items():
        coupling[i - 1, j - 1] = coupling[j - 1, i - 1] = kappa
    pump = np.full(n, case.laser.A)
    for site, value in case.network.pumps.items():
        pump[site - 1] = value
    return n, coupling, pump


def field_equations(case: Case):
    """dy/dt for y = (G, Q, Re E, Im E), via complex fields."""
    n, coupling, pump = _setup(case)
    la = case.laser

    def f(t, y):
        gain, absorption = y[:n], y[n : 2 * n]
        e = y[2 * n : 3 * n] + 1j * y[3 * n :]
        intensity = np.abs(e) ** 2
        de = 0.5 * (1 - 1j * la.alpha) * (gain - absorption - 1) * e + 1j * (coupling @ e)
        dg = la.gamma * (pump - gain * (1 + intensity))
        dq = la.gamma * (la.B - absorption * (1 + la.a * intensity))
        return np.concatenate([dg, dq, de.real, de.imag])

    return f, n, pump


def _kicked(y: np.ndarray, case: Case, n: int, time: float) -> np.ndarray:
    y = y.copy()
    for k in case.kicks:
        if k.time == time:
            z = k.amplitude * np.exp(1j * np.radians(k.phase))
            y[2 * n + k.site - 1] += z.real
            y[3 * n + k.site - 1] += z.imag
    return y


def simulate(case: Case, sample: float = 0.05) -> dict:
    """Spikes per site as lists of (time, peak), and a function giving the intensities at any times."""
    f, n, pump = field_equations(case)
    y = np.concatenate([pump, np.full(n, case.laser.B), np.zeros(2 * n)])
    edges = sorted({k.time for k in case.kicks} | {0.0, case.duration})
    spikes: list[list[tuple[float, float]]] = [[] for _ in range(n)]
    segments = []
    for t0, t1 in zip(edges[:-1], edges[1:], strict=True):
        y = _kicked(y, case, n, t0)
        sol = solve_ivp(f, (t0, t1), y, method="LSODA", rtol=1e-10, atol=1e-13, dense_output=True)
        t = np.linspace(t0, t1, max(int((t1 - t0) / sample) + 1, 5))
        dense = sol.sol(t)
        intensity = dense[2 * n : 3 * n] ** 2 + dense[3 * n :] ** 2
        step = t[1] - t[0]
        for site in range(n):
            x = intensity[site]
            for i in np.nonzero((x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:]) & (x[1:-1] >= case.threshold * 0.9))[0] + 1:
                denom = x[i - 1] - 2 * x[i] + x[i + 1]
                shift = 0.5 * (x[i - 1] - x[i + 1]) / denom
                peak = x[i] - 0.25 * (x[i - 1] - x[i + 1]) * shift
                if peak >= case.threshold:
                    spikes[site].append((float(t[i] + shift * step), float(peak)))
        segments.append((t0, t1, sol.sol))
        y = sol.y[:, -1]

    def intensity_at(times):
        times = np.asarray(times, dtype=float)
        out = np.zeros((n, len(times)))
        for t0, t1, dense in segments:
            mask = (times >= t0) & (times <= t1)
            if mask.any():
                v = dense(times[mask])
                out[:, mask] = v[2 * n : 3 * n] ** 2 + v[3 * n :] ** 2
        return out

    return {"spikes": spikes, "intensity": intensity_at}


def rk4(case: Case, step: float = 0.01) -> np.ndarray:
    """State at the end of the run by classical Runge-Kutta with a fixed step. For short runs only."""
    f, n, pump = field_equations(case)
    y = np.concatenate([pump, np.full(n, case.laser.B), np.zeros(2 * n)])
    edges = sorted({k.time for k in case.kicks} | {0.0, case.duration})
    for t0, t1 in zip(edges[:-1], edges[1:], strict=True):
        y = _kicked(y, case, n, t0)
        count = max(int(round((t1 - t0) / step)), 1)
        h = (t1 - t0) / count
        for _ in range(count):
            k1 = f(0.0, y)
            k2 = f(0.0, y + 0.5 * h * k1)
            k3 = f(0.0, y + 0.5 * h * k2)
            k4 = f(0.0, y + h * k3)
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return y


def dark_intensities(case: Case, times) -> np.ndarray:
    """Intensities while every site is dark: the field equations are then linear with constant coefficients.

    With gain and absorption at rest, dE/dt = M E with M = diag((1 - i alpha)(A_j - B - 1) / 2) + i K, solved by
    diagonalising M. Valid for kicks so weak that they bleach nothing.
    """
    n, coupling, pump = _setup(case)
    la = case.laser
    m = np.diag(0.5 * (1 - 1j * la.alpha) * (pump - la.B - 1)) + 1j * coupling
    values, vectors = np.linalg.eig(m)
    inverse = np.linalg.inv(vectors)
    times = np.asarray(times, dtype=float)
    e = np.zeros((n, len(times)), dtype=complex)
    for k in case.kicks:
        start = np.zeros(n, dtype=complex)
        start[k.site - 1] = k.amplitude * np.exp(1j * np.radians(k.phase))
        weights = inverse @ start
        after = times >= k.time
        e[:, after] += vectors @ (weights[:, None] * np.exp(np.outer(values, times[after] - k.time)))
    return np.abs(e) ** 2
