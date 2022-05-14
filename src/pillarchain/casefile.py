"""Reader for network files.

    title <text>
    laser A=<pump> B=<absorption> a=<saturation ratio> gamma=<carrier rate> alpha=<linewidth factor>
    sites <count>                      add uncoupled sites (numbered on from the last one)
    path <first> <last> kappa=<rate>   link each site of the range to the next
    link <i> <j> kappa=<rate>
    grid <nx> <ny> kappa=<rate>        add nx * ny sites, row by row, linked to their nearest neighbours
    pump <first> [<last>] A=<pump>     a different pump for one site or a range
    kick <site> time=<t> amplitude=<s> [phase=<degrees>]
    run <duration>
    threshold <intensity>              what counts as a spike (default 5)
    expect <kind> <args...>

`#` starts a comment; the comment lines at the top of a file are its description.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import Laser, Network
from .simulate import Kick


@dataclass
class Expectation:
    kind: str
    args: list[str]
    line: int


@dataclass
class Case:
    title: str = ""
    laser: Laser = field(default_factory=Laser)
    network: Network = field(default_factory=Network)
    kicks: list[Kick] = field(default_factory=list)
    duration: float = 0.0
    threshold: float = 5.0
    expectations: list[Expectation] = field(default_factory=list)


def _split(
    words: list[str], positional: int, allowed: tuple[str, ...], owner: str
) -> tuple[list[float], dict[str, float]]:
    """Leading numbers and trailing key=value pairs of a statement."""
    numbers, pairs = [], {}
    for w in words:
        key, sep, value = w.partition("=")
        try:
            if sep:
                if key not in allowed:
                    raise ValueError(f"{owner} does not have '{key}'")
                pairs[key] = float(value)
            else:
                numbers.append(float(w))
        except ValueError as err:
            if "does not have" in str(err):
                raise
            raise ValueError(f"'{w}' is not a number") from None
    if len(numbers) != positional:
        raise ValueError(f"{owner} takes {positional} number{'' if positional == 1 else 's'} before its options")
    return numbers, pairs


def _site(value: float) -> int:
    if value != int(value) or value < 1:
        raise ValueError(f"'{value:g}' is not a site number")
    return int(value)


def _need(pairs: dict[str, float], key: str, owner: str) -> float:
    if key not in pairs:
        raise ValueError(f"{owner} needs {key}=...")
    return pairs[key]


def _statement(case: Case, line: str, words: list[str]) -> None:
    key, rest = words[0], words[1:]
    if key == "title":
        case.title = line[5:].strip()
    elif key == "laser":
        _, pairs = _split(rest, 0, ("A", "B", "a", "gamma", "alpha"), "laser")
        current = {
            "A": case.laser.A,
            "B": case.laser.B,
            "a": case.laser.a,
            "gamma": case.laser.gamma,
            "alpha": case.laser.alpha,
        }
        case.laser = Laser(**(current | pairs))
    elif key == "sites":
        (count,), _ = _split(rest, 1, (), "sites")
        case.network.add_sites(_site(count))
    elif key in ("path", "link"):
        (i, j), pairs = _split(rest, 2, ("kappa",), key)
        build = case.network.path if key == "path" else case.network.link
        build(_site(i), _site(j), _need(pairs, "kappa", key))
    elif key == "grid":
        (nx, ny), pairs = _split(rest, 2, ("kappa",), "grid")
        case.network.grid(_site(nx), _site(ny), _need(pairs, "kappa", "grid"))
    elif key == "pump":
        numbers, pairs = _split(rest, len([w for w in rest if "=" not in w]), ("A",), "pump")
        if len(numbers) not in (1, 2):
            raise ValueError("pump takes a site or a range of sites")
        first, last = _site(numbers[0]), _site(numbers[-1])
        if last < first:
            raise ValueError("a range needs its first site below its last")
        for site in range(first, last + 1):
            case.network.set_pump(site, _need(pairs, "A", "pump"))
    elif key == "kick":
        (site,), pairs = _split(rest, 1, ("time", "amplitude", "phase"), "kick")
        case.kicks.append(
            Kick(_site(site), pairs.get("time", 0.0), _need(pairs, "amplitude", "kick"), pairs.get("phase", 0.0))
        )
    elif key == "run":
        (duration,), _ = _split(rest, 1, (), "run")
        if duration <= 0:
            raise ValueError("the duration must be positive")
        case.duration = duration
    elif key == "threshold":
        (value,), _ = _split(rest, 1, (), "threshold")
        if value <= 0:
            raise ValueError("the threshold must be positive")
        case.threshold = value
    else:
        raise ValueError(f"unknown statement '{key}'")


def parse(text: str) -> Case:
    """Parses a case. Raises ValueError with the line number on any error."""
    case = Case()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        words = line.split()
        try:
            if words[0] == "expect":
                if len(words) < 2:
                    raise ValueError("expect needs a kind")
                case.expectations.append(Expectation(words[1], words[2:], number))
            else:
                _statement(case, line, words)
        except ValueError as err:
            raise ValueError(f"line {number}: {err}") from None
    if case.network.sites == 0:
        raise ValueError("the file defines no sites")
    if case.duration <= 0:
        raise ValueError("the file has no run statement")
    for kick in case.kicks:
        if not 1 <= kick.site <= case.network.sites:
            raise ValueError(f"a kick names site {kick.site}, which does not exist")
        if not 0 <= kick.time < case.duration:
            raise ValueError(f"the kick at time {kick.time:g} lies outside the run")
    return case


def load(path: Path | str) -> Case:
    return parse(Path(path).read_text())
