"""Expectations of a network file, checked against its simulation.

fired <site> yes|no
count <site> <n>                     number of spikes of one site
each <first> <last> <n>              every site of the range spiked n times
silent <first> <last>                no site of the range spiked
total <n>                            spikes in the whole network
arrival <site> <t> <tol>             time of the first spike
peak <site> <I> <reltol>             peak intensity of the first spike
delay <i> <j> <dt> <tol>             arrival at j minus arrival at i
order <site> <site> ...              first spikes in this order
together <i> <j> <tol>               first spikes within tol of each other
last <t> <tol>                       time of the last spike anywhere
quiet_after <t>                      no spike after t
intensity <site> <t> <I> <reltol>    intensity of a site at a time
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .casefile import Case, Expectation
from .simulate import Result


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def _num(e: Expectation, i: int) -> float:
    try:
        return float(e.args[i])
    except ValueError:
        raise ValueError(f"'{e.args[i]}' is not a number") from None


def _arity(e: Expectation, n: int) -> None:
    if len(e.args) != n:
        raise ValueError(f"'{e.kind}' takes {n} argument{'' if n == 1 else 's'}")


def _site(e: Expectation, i: int, r: Result) -> int:
    v = _num(e, i)
    if v != int(v) or not 1 <= v <= r.sites:
        raise ValueError(f"site {e.args[i]} does not exist")
    return int(v)


def _arrival(r: Result, site: int) -> float:
    t = r.arrival(site)
    if t is None:
        raise ValueError(f"site {site} never spiked")
    return t


def _range(e: Expectation, r: Result) -> range:
    first, last = _site(e, 0, r), _site(e, 1, r)
    if last < first:
        raise ValueError("a range needs its first site below its last")
    return range(first, last + 1)


def _one(r: Result, e: Expectation) -> tuple[bool, str]:
    k = e.kind
    if k == "fired":
        _arity(e, 2)
        if e.args[1] not in ("yes", "no"):
            raise ValueError("'fired' takes a site and yes or no")
        n = r.count(_site(e, 0, r))
        return (n > 0) == (e.args[1] == "yes"), f"{n} spike(s)"
    if k == "count":
        _arity(e, 2)
        n = r.count(_site(e, 0, r))
        return n == _num(e, 1), f"{n} spike(s)"
    if k in ("each", "silent"):
        _arity(e, 3 if k == "each" else 2)
        want = _num(e, 2) if k == "each" else 0
        counts = [r.count(s) for s in _range(e, r)]
        odd = [f"site {s}: {c}" for s, c in zip(_range(e, r), counts, strict=True) if c != want]
        return not odd, "all as expected" if not odd else ", ".join(odd[:6])
    if k == "total":
        _arity(e, 1)
        return r.total == _num(e, 0), f"{r.total} spike(s)"
    if k == "arrival":
        _arity(e, 3)
        t = _arrival(r, _site(e, 0, r))
        return abs(t - _num(e, 1)) <= _num(e, 2), f"{t:.6f}, expected {_num(e, 1):.6f}, off by {t - _num(e, 1):.2e}"
    if k == "peak":
        _arity(e, 3)
        site = _site(e, 0, r)
        _arrival(r, site)
        peak = r.spikes[site - 1][0][1]
        return abs(peak / _num(e, 1) - 1) <= _num(
            e, 2
        ), f"{peak:.8g}, expected {_num(e, 1):.8g}, relative error {peak / _num(e, 1) - 1:.2e}"
    if k == "delay":
        _arity(e, 4)
        d = _arrival(r, _site(e, 1, r)) - _arrival(r, _site(e, 0, r))
        return abs(d - _num(e, 2)) <= _num(e, 3), f"{d:.6f}, expected {_num(e, 2):.6f}, off by {d - _num(e, 2):.2e}"
    if k == "order":
        if len(e.args) < 2:
            raise ValueError("'order' takes at least two sites")
        times = [_arrival(r, _site(e, i, r)) for i in range(len(e.args))]
        return all(a < b for a, b in zip(times[:-1], times[1:], strict=True)), ", ".join(f"{t:.2f}" for t in times)
    if k == "together":
        _arity(e, 3)
        d = _arrival(r, _site(e, 1, r)) - _arrival(r, _site(e, 0, r))
        return abs(d) <= _num(e, 2), f"apart by {d:.3e}"
    if k == "last":
        _arity(e, 2)
        if r.last_spike is None:
            raise ValueError("nothing spiked")
        return abs(r.last_spike - _num(e, 0)) <= _num(e, 1), f"{r.last_spike:.6f}, expected {_num(e, 0):.6f}"
    if k == "quiet_after":
        _arity(e, 1)
        late = r.last_spike
        return late is None or late <= _num(e, 0), "nothing spiked" if late is None else f"last spike at {late:.3f}"
    if k == "intensity":
        _arity(e, 4)
        site, t = _site(e, 0, r), _num(e, 1)
        if not 0 <= t <= r.duration:
            raise ValueError(f"time {t:g} lies outside the run")
        got = float(r.intensity(np.array([t]))[site - 1, 0])
        return abs(got / _num(e, 2) - 1) <= _num(
            e, 3
        ), f"{got:.8g}, expected {_num(e, 2):.8g}, relative error {got / _num(e, 2) - 1:.2e}"
    raise ValueError(f"unknown expectation '{k}'")


def evaluate(case: Case, result: Result) -> list[Check]:
    """A malformed expectation becomes a failed check with its line number; it does not stop the others."""
    out = []
    for e in case.expectations:
        name = " ".join([e.kind, *e.args])
        try:
            passed, detail = _one(result, e)
        except ValueError as err:
            passed, detail = False, f"line {e.line}: {err}"
        out.append(Check(name, bool(passed), detail))
    return out
