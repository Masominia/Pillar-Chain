"""Coupled lasers with saturable absorber.

Each site j carries a complex field E_j, a gain G_j and an absorption Q_j:

    dE_j/dt = (1 - i alpha) (G_j - Q_j - 1) E_j / 2 + i sum_k kappa_jk E_k
    dG_j/dt = gamma (A_j - G_j - G_j |E_j|^2)
    dQ_j/dt = gamma (B - Q_j - a Q_j |E_j|^2)

Time is in photon lifetimes. alpha is the linewidth enhancement factor, kappa_jk the evanescent coupling rate
between neighbouring cavities (real and symmetric: it exchanges light with a quarter-turn of phase).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Laser:
    A: float = 6.5
    B: float = 5.8
    a: float = 1.8
    gamma: float = 0.01
    alpha: float = 2.0

    def __post_init__(self):
        if not (self.A >= 0 and self.B >= 0 and self.a > 0 and self.gamma > 0):
            raise ValueError("the laser needs A >= 0, B >= 0, a > 0 and gamma > 0")


@dataclass
class Network:
    """Sites numbered from 1, symmetric links with their coupling rates, and pumps that differ from the laser's."""

    sites: int = 0
    links: dict[tuple[int, int], float] = field(default_factory=dict)
    pumps: dict[int, float] = field(default_factory=dict)

    def _check(self, site: int) -> None:
        if not 1 <= site <= self.sites:
            raise ValueError(f"site {site} does not exist (there are {self.sites})")

    def add_sites(self, count: int) -> None:
        if count < 1:
            raise ValueError("the number of sites must be positive")
        self.sites += count

    def link(self, i: int, j: int, kappa: float) -> None:
        self._check(i)
        self._check(j)
        if i == j:
            raise ValueError("a site cannot be linked to itself")
        if kappa < 0:
            raise ValueError("a coupling rate cannot be negative")
        self.links[(min(i, j), max(i, j))] = kappa

    def path(self, first: int, last: int, kappa: float) -> None:
        if last <= first:
            raise ValueError("a path needs its first site below its last")
        for i in range(first, last):
            self.link(i, i + 1, kappa)

    def grid(self, nx: int, ny: int, kappa: float) -> None:
        """Adds nx * ny sites, row by row, with links between nearest neighbours."""
        if nx < 1 or ny < 1:
            raise ValueError("a grid needs positive sizes")
        base = self.sites
        self.add_sites(nx * ny)
        for iy in range(ny):
            for ix in range(nx):
                me = base + iy * nx + ix + 1
                if ix + 1 < nx:
                    self.link(me, me + 1, kappa)
                if iy + 1 < ny:
                    self.link(me, me + nx, kappa)

    def set_pump(self, site: int, pump: float) -> None:
        self._check(site)
        if pump < 0:
            raise ValueError("a pump cannot be negative")
        self.pumps[site] = pump

    def coupling_matrix(self) -> np.ndarray:
        m = np.zeros((self.sites, self.sites))
        for (i, j), kappa in self.links.items():
            m[i - 1, j - 1] = m[j - 1, i - 1] = kappa
        return m

    def pump_vector(self, laser: Laser) -> np.ndarray:
        pump = np.full(self.sites, laser.A)
        for site, value in self.pumps.items():
            pump[site - 1] = value
        return pump

    def neighbours(self, site: int) -> list[int]:
        return sorted(j if i == site else i for (i, j) in self.links if site in (i, j))


def rest_state(network: Network, laser: Laser) -> np.ndarray:
    """All sites dark with gain and absorption relaxed: the state vector (G, Q, Re E, Im E)."""
    n = network.sites
    return np.concatenate([network.pump_vector(laser), np.full(n, laser.B), np.zeros(2 * n)])


def make_rhs(network: Network, laser: Laser):
    """The vector field on the state (G, Q, Re E, Im E), each of length `sites`."""
    n = network.sites
    coupling = network.coupling_matrix()
    pump = network.pump_vector(laser)
    gamma, absorption0, a, alpha = laser.gamma, laser.B, laser.a, laser.alpha

    def rhs(t, y):
        gain, absorption, re, im = y[:n], y[n : 2 * n], y[2 * n : 3 * n], y[3 * n :]
        intensity = re * re + im * im
        net = 0.5 * (gain - absorption - 1.0)
        # (1 - i alpha) net (re + i im) + i coupling (re + i im)
        d_re = net * (re + alpha * im) - coupling @ im
        d_im = net * (im - alpha * re) + coupling @ re
        return np.concatenate(
            [
                gamma * (pump - gain - gain * intensity),
                gamma * (absorption0 - absorption - a * absorption * intensity),
                d_re,
                d_im,
            ]
        )

    return rhs
