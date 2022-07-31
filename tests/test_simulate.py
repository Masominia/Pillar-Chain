import numpy as np
import pytest

from pillarchain.model import Laser, Network
from pillarchain.simulate import Kick, simulate
from pillarchain.studies import chain


def one():
    net = Network()
    net.add_sites(1)
    return net


def test_nothing_happens_without_a_kick():
    r = simulate(chain(4, 0.06), Laser(), [], 300.0)
    assert r.total == 0 and r.last_spike is None and r.arrival(2) is None


def test_single_pillar_threshold():
    assert simulate(one(), Laser(), [Kick(1, 0.0, 1.2)], 400.0).total == 0
    r = simulate(one(), Laser(), [Kick(1, 0.0, 2.0)], 400.0)
    assert r.total == 1 and r.arrival(1) == pytest.approx(12.5825, abs=1e-3)
    assert r.spikes[0][0][1] == pytest.approx(58.75, abs=0.02)


def test_stronger_kick_fires_sooner():
    times = [simulate(one(), Laser(), [Kick(1, 0.0, a)], 400.0).arrival(1) for a in (1.4, 2.0, 3.0)]
    assert times[0] > times[1] > times[2]


def test_kick_time_shifts_everything():
    a = simulate(chain(4, 0.06), Laser(), [Kick(1, 0.0, 2.0)], 400.0)
    b = simulate(chain(4, 0.06), Laser(), [Kick(1, 50.0, 2.0)], 450.0)
    for site in range(1, 5):
        assert b.arrival(site) - a.arrival(site) == pytest.approx(50.0, abs=1e-5)


def test_chain_fires_in_order_once():
    r = simulate(chain(6, 0.06), Laser(), [Kick(1, 0.0, 2.0)], 600.0)
    arrivals = [r.arrival(s) for s in range(1, 7)]
    assert r.total == 6 and arrivals == sorted(arrivals)


def test_weak_chain_does_not_propagate():
    r = simulate(chain(6, 0.03), Laser(), [Kick(1, 0.0, 2.0)], 1500.0)
    assert r.count(1) == 1 and r.total == 1


def test_intensity_shape_and_values():
    r = simulate(chain(3, 0.06), Laser(), [Kick(2, 10.0, 2.0)], 100.0)
    image = r.intensity(np.array([0.0, 5.0, 10.0, 10.5]))
    assert image.shape == (3, 4)
    assert image[:, :2].max() == 0 and image[1, 2] == pytest.approx(4.0)
    assert image[0, 3] == pytest.approx(image[2, 3]) and image[0, 3] > 0


def test_kick_adds_coherently():
    # two simultaneous kicks of opposite phase on one site cancel
    r = simulate(one(), Laser(), [Kick(1, 0.0, 2.0), Kick(1, 0.0, 2.0, 180.0)], 300.0)
    assert r.total == 0


def test_spike_peak_is_a_maximum():
    r = simulate(one(), Laser(), [Kick(1, 0.0, 2.0)], 200.0)
    t, peak = r.spikes[0][0]
    near = r.intensity(np.array([t - 0.05, t, t + 0.05]))[0]
    assert near[1] == pytest.approx(peak, rel=1e-9) and near[0] < peak > near[2]


def test_threshold_decides_what_counts():
    low = simulate(one(), Laser(), [Kick(1, 0.0, 2.0)], 200.0, threshold=100.0)
    assert low.total == 0
