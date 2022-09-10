import numpy as np
import pytest

from pillarchain import reference
from pillarchain.casefile import parse
from pillarchain.compare import compare
from pillarchain.model import make_rhs
from pillarchain.runner import run_case

CHAIN = "sites 4\npath 1 4 kappa=0.06\nkick 1 amplitude=2\nrun 300\n"


def test_two_forms_of_the_equations_agree():
    case = parse("laser alpha=3\nsites 4\npath 1 4 kappa=0.07\npump 2 A=6.1\nrun 10\n")
    y = np.random.default_rng(5).normal(size=16)
    f, n, _ = reference.field_equations(case)
    assert n == 4 and np.allclose(f(0.0, y), make_rhs(case.network, case.laser)(0.0, y), atol=1e-14)


def test_reference_finds_the_same_spikes():
    case = parse(CHAIN)
    mine, theirs = run_case(case).spikes, reference.simulate(case)["spikes"]
    assert [len(s) for s in mine] == [len(s) for s in theirs] == [1, 1, 1, 1]
    for a, b in zip(mine, theirs, strict=True):
        assert a[0][0] == pytest.approx(b[0][0], abs=1e-3) and a[0][1] == pytest.approx(b[0][1], rel=1e-5)


def test_compare_reports_agreement():
    case = parse(CHAIN)
    out = compare(case, run_case(case))
    assert not out["outside"] and set(out["differences"]) == {"spike time", "spike peak", "dark intensity"}


def test_compare_notices_a_missing_spike():
    case = parse(CHAIN)
    result = run_case(case)
    result.spikes[3] = []
    assert any("site 4" in line for line in compare(case, result)["outside"])


def test_compare_notices_a_shifted_spike():
    case = parse(CHAIN)
    result = run_case(case)
    t, peak = result.spikes[2][0]
    result.spikes[2] = [(t + 0.05, peak)]
    assert any("spike time" in line for line in compare(case, result)["outside"])


def test_dark_closed_form_for_two_cavities():
    # two identical cavities: light beats between them as cos^2 and sin^2 of kappa t under a common decay
    case = parse("sites 2\nlink 1 2 kappa=0.2\nkick 1 amplitude=0.001\nrun 20\n")
    t = np.array([1.0, 4.0, 9.0])
    decay = 1e-6 * np.exp((6.5 - 5.8 - 1) * t)
    got = reference.dark_intensities(case, t)
    assert np.allclose(got[0], decay * np.cos(0.2 * t) ** 2, rtol=1e-12)
    assert np.allclose(got[1], decay * np.sin(0.2 * t) ** 2, rtol=1e-12)


def test_engine_follows_the_dark_closed_form():
    case = parse("sites 3\npath 1 3 kappa=0.1\nkick 2 amplitude=0.001\nrun 30\n")
    t = np.array([2.0, 7.0, 15.0])
    assert np.allclose(run_case(case).intensity(t), reference.dark_intensities(case, t), rtol=2e-4)


def test_fixed_step_integration_approaches_the_adaptive_one():
    case = parse("sites 2\nlink 1 2 kappa=0.06\nkick 1 amplitude=2\nrun 40\n")
    final = run_case(case).segments[-1][2](40.0)
    assert np.abs(reference.rk4(case, 0.05) - final).max() < 1e-6
