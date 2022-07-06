import pytest

from pillarchain.casefile import parse
from pillarchain.expect import evaluate
from pillarchain.runner import run_case

BASE = "sites 5\npath 1 4 kappa=0.06\nkick 1 amplitude=2\nrun 400\n"


@pytest.fixture(scope="module")
def result():
    return run_case(parse(BASE))


def verdict(result, line):
    case = parse(BASE + "expect " + line + "\n")
    (check,) = evaluate(case, result)
    return check


@pytest.mark.parametrize(
    "line, passed",
    [
        ("fired 1 yes", True),
        ("fired 5 yes", False),
        ("fired 5 no", True),
        ("count 2 1", True),
        ("count 2 2", False),
        ("each 1 4 1", True),
        ("each 1 5 1", False),
        ("silent 5 5", True),
        ("silent 4 5", False),
        ("total 4", True),
        ("total 5", False),
        ("arrival 1 12.96 0.01", True),
        ("arrival 1 13.5 0.01", False),
        ("peak 1 58.5 0.02", True),
        ("peak 1 50 0.02", False),
        ("order 1 2 3 4", True),
        ("order 2 1", False),
        ("together 1 2 100", True),
        ("together 1 2 1", False),
        ("quiet_after 200", True),
        ("quiet_after 20", False),
        ("intensity 1 0 4 1e-9", True),
        ("intensity 2 0.5 4 0.1", False),
    ],
)
def test_kinds(result, line, passed):
    assert verdict(result, line).passed is passed


def test_delay_and_last_agree_with_arrivals(result):
    d = result.arrival(3) - result.arrival(2)
    assert verdict(result, f"delay 2 3 {d:.6f} 1e-5").passed
    assert not verdict(result, f"delay 2 3 {d + 1:.6f} 1e-5").passed
    assert verdict(result, f"last {result.arrival(4):.6f} 1e-5").passed


@pytest.mark.parametrize(
    "line, message",
    [
        ("fired 1 maybe", "yes or no"),
        ("count 9 1", "site 9 does not exist"),
        ("count 1", "takes 2 arguments"),
        ("arrival 5 10 1", "site 5 never spiked"),
        ("arrival 1 soon 1", "'soon' is not a number"),
        ("each 4 2 1", "first site below its last"),
        ("order 1", "at least two sites"),
        ("intensity 1 900 1 0.1", "outside the run"),
        ("colour 1 red", "unknown expectation 'colour'"),
    ],
)
def test_malformed_expectations_fail_with_their_line(result, line, message):
    check = verdict(result, line)
    assert not check.passed and "line 5" in check.detail and message in check.detail


def test_one_bad_expectation_does_not_stop_the_others(result):
    case = parse(BASE + "expect nonsense\nexpect total 4\n")
    checks = evaluate(case, result)
    assert [c.passed for c in checks] == [False, True]
