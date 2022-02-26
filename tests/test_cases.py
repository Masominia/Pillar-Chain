import pytest

from pillarchain import cases
from pillarchain.cases import ROOT
from pillarchain.runner import run_file

ALL = cases.discover(ROOT / "cases")


def test_library_is_present_and_described():
    assert len(ALL) >= 90
    for path in ALL:
        assert len(cases.notes(path)) >= 2, f"{path.name} has no description"
        assert "expect " in path.read_text(), f"{path.name} checks nothing"


def test_families():
    fam = {"rings": ["ring_"], "chains": ["chain_"]}
    assert cases.family_of("ring_single_n12", fam) == "rings"
    assert cases.family_of("chain_long20", fam) == "chains"
    assert cases.family_of("grid_corner", fam) == "other"


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.stem)
def test_every_case_meets_its_expectations(path):
    record, _, _ = run_file(path)
    assert record["checks"], "no expectations evaluated"
    failed = [c for c in record["checks"] if c["status"] != "PASS"]
    assert not failed, failed
