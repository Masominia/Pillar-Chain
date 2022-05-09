import numpy as np
import pytest

from pillarchain import studies
from pillarchain.model import Laser

LASER = Laser()


def test_propagation_has_a_threshold():
    assert studies.propagates(LASER, 0.06) and not studies.propagates(LASER, 0.03)


def test_critical_coupling():
    k = studies.critical_coupling(LASER, low=0.04, high=0.044, tolerance=1e-4)
    assert k == pytest.approx(0.04186, abs=1e-4)


def test_critical_coupling_needs_a_bracket():
    with pytest.raises(ValueError):
        studies.critical_coupling(LASER, low=0.05, high=0.06)


def test_speed_grows_with_coupling():
    t = studies.speed(LASER, [0.03, 0.05, 0.08])
    assert np.isnan(t["delay per site"].iloc[0])
    assert t["delay per site"].iloc[1] > t["delay per site"].iloc[2] > 5


def test_refractory_time_is_about_a_carrier_lifetime():
    assert 100 < studies.refractory_time(LASER, 2.0, low=100.0, high=200.0, tolerance=2.0) < 180


def test_symmetries_hold():
    s = studies.symmetry(LASER, sites=5)
    assert s["phase"] < 1e-5 and s["mirror"] < 1e-5


def test_step_convergence_is_fourth_order():
    t = studies.step_convergence("sites 2\nlink 1 2 kappa=0.06\nkick 1 amplitude=2\nrun 40\n")
    assert all(3.5 < o < 4.5 for o in t["order"].dropna())


def test_ring_holds_a_slowed_pulse():
    c = studies.circulation(LASER, [12], 0.06, 185.0, 17.2357, duration=2500.0)
    assert c["round trips"].iloc[0] >= 4
    assert c["round trip"].iloc[0] == pytest.approx(276.7, abs=0.5) and c["over open chain"].iloc[0] > 1.2


def test_ring_without_a_held_pulse_has_no_round_trip():
    c = studies.circulation(LASER, [12], 0.06, 150.0, 17.2357, duration=1500.0)
    assert c["round trips"].iloc[0] == 0 and "round trip" not in c


def test_gates_read_records():
    records = {
        "junction_a": {
            "kicks": [{"site": 1, "time": 0.0, "phase": 0.0}, {"site": 6, "time": 5.0, "phase": 90.0}],
            "spikes": {"16": [[180.0, 55.0]]},
        },
        "junction_b": {"kicks": [{"site": 6, "time": 0.0, "phase": 0.0}], "spikes": {}},
    }
    g = studies.gates(records).set_index("case")
    assert g.loc["junction_a", "output"] == "yes" and g.loc["junction_a", "lag"] == 5.0
    assert g.loc["junction_a", "phase"] == 90.0
    assert g.loc["junction_b", "output"] == "no" and g.loc["junction_b", "input 1"] == "no"
