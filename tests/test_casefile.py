import pytest

from pillarchain.casefile import load, parse

GOOD = """# a comment
title Two arms
laser gamma=0.02
sites 4
path 1 4 kappa=0.06   # trailing comment
link 4 1 kappa=0.03
pump 2 3 A=6.2
kick 1 amplitude=2
kick 3 time=40 amplitude=1.5 phase=90
run 500
threshold 4
expect total 4
expect fired 1 yes
"""


def test_parse_reads_everything():
    c = parse(GOOD)
    assert c.title == "Two arms" and c.laser.gamma == 0.02 and c.laser.A == 6.5
    assert c.network.sites == 4 and c.network.links[(1, 4)] == 0.03 and len(c.network.links) == 4
    assert c.network.pumps == {2: 6.2, 3: 6.2}
    assert [(k.site, k.time, k.amplitude, k.phase) for k in c.kicks] == [(1, 0.0, 2.0, 0.0), (3, 40.0, 1.5, 90.0)]
    assert c.duration == 500 and c.threshold == 4
    assert [(e.kind, e.args, e.line) for e in c.expectations] == [("total", ["4"], 12), ("fired", ["1", "yes"], 13)]


def test_grid_statement():
    c = parse("grid 3 2 kappa=0.05\nrun 10\n")
    assert c.network.sites == 6 and len(c.network.links) == 7


@pytest.mark.parametrize(
    "text, message",
    [
        ("sites 2\nlink 1 2\nrun 10", "line 2: link needs kappa"),
        ("sites 2\nlink 1 3 kappa=0.1\nrun 10", "line 2: site 3 does not exist"),
        ("sites 2\nwire 1 2\nrun 10", "line 2: unknown statement 'wire'"),
        ("sites two\nrun 10", "line 1: 'two' is not a number"),
        ("sites 2\nlaser beta=1\nrun 10", "line 2: laser does not have 'beta'"),
        ("sites 2\nkick 1 time=3\nrun 10", "line 2: kick needs amplitude"),
        ("sites 2\nkick 1.5 amplitude=2\nrun 10", "line 2: '1.5' is not a site number"),
        ("sites 2\nrun -5", "line 2: the duration must be positive"),
        ("sites 2\nrun 10\nexpect", "line 3: expect needs a kind"),
        ("sites 2\nrun 10 20", "line 2: run takes 1 number before its options"),
        ("sites 3\npump 3 1 A=6\nrun 10", "line 2: a range needs its first site below its last"),
        ("sites 2\nthreshold 0\nrun 10", "line 2: the threshold must be positive"),
        ("run 10", "the file defines no sites"),
        ("sites 2", "the file has no run statement"),
        ("sites 2\nkick 5 amplitude=1\nrun 10", "a kick names site 5"),
        ("sites 2\nkick 1 time=20 amplitude=1\nrun 10", "the kick at time 20 lies outside the run"),
    ],
)
def test_errors_name_the_line(text, message):
    with pytest.raises(ValueError, match=message):
        parse(text)


def test_load_missing_file(tmp_path):
    with pytest.raises(OSError):
        load(tmp_path / "nothing.pil")


def test_load_reads_a_file(tmp_path):
    p = tmp_path / "x.pil"
    p.write_text("sites 1\nrun 5\n")
    assert load(p).network.sites == 1
