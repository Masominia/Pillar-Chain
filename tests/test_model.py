import numpy as np
import pytest

from pillarchain.model import Laser, Network, make_rhs, rest_state


def chain(n, kappa=0.06):
    net = Network()
    net.add_sites(n)
    net.path(1, n, kappa)
    return net


def test_network_building():
    net = chain(4)
    assert net.sites == 4 and len(net.links) == 3
    assert net.neighbours(2) == [1, 3] and net.neighbours(1) == [2]
    m = net.coupling_matrix()
    assert np.allclose(m, m.T) and m[0, 1] == 0.06 and m[0, 2] == 0


def test_grid_links_nearest_neighbours():
    net = Network()
    net.grid(4, 3, 0.05)
    assert net.sites == 12 and len(net.links) == 3 * 3 + 4 * 2
    assert net.neighbours(6) == [2, 5, 7, 10] and net.neighbours(1) == [2, 5]


def test_grid_after_sites_is_offset():
    net = Network()
    net.add_sites(5)
    net.grid(2, 2, 0.05)
    assert net.sites == 9 and net.neighbours(6) == [7, 8]


@pytest.mark.parametrize(
    "build",
    [
        lambda n: n.link(1, 1, 0.1),
        lambda n: n.link(1, 9, 0.1),
        lambda n: n.link(1, 2, -0.1),
        lambda n: n.path(3, 2, 0.1),
        lambda n: n.set_pump(7, 6.0),
        lambda n: n.set_pump(1, -1.0),
        lambda n: n.add_sites(0),
        lambda n: n.grid(0, 3, 0.1),
    ],
)
def test_bad_networks_are_refused(build):
    with pytest.raises(ValueError):
        build(chain(4))


def test_pump_vector():
    net = chain(3)
    net.set_pump(2, 6.0)
    assert net.pump_vector(Laser()).tolist() == [6.5, 6.0, 6.5]


def test_rest_state_is_stationary():
    net, laser = chain(5), Laser()
    y = rest_state(net, laser)
    assert np.abs(make_rhs(net, laser)(0.0, y)).max() == 0


def test_rest_state_is_stable_below_threshold():
    # net gain A - B - 1 < 0: a small field decays
    net, laser = Network(), Laser()
    net.add_sites(1)
    y = rest_state(net, laser)
    y[2] = 1e-3
    d = make_rhs(net, laser)(0.0, y)
    assert d[2] < 0 and d[2] == pytest.approx(0.5 * (6.5 - 5.8 - 1) * 1e-3)


def test_field_equation_matches_complex_form():
    rng = np.random.default_rng(3)
    net, laser = chain(4, 0.07), Laser(alpha=3.0)
    y = rng.normal(size=16)
    d = make_rhs(net, laser)(0.0, y)
    e = y[8:12] + 1j * y[12:]
    want = 0.5 * (1 - 3j) * (y[:4] - y[4:8] - 1) * e + 1j * net.coupling_matrix() @ e
    assert np.allclose(d[8:12] + 1j * d[12:], want)


def test_coupling_conserves_total_field_energy():
    # with gain and loss balanced (G - Q - 1 = 0) the coupling alone moves light without creating it
    net, laser = chain(3, 0.2), Laser()
    y = np.concatenate([np.full(3, 7.8), np.full(3, 6.8), [0.3, -0.1, 0.2], [0.05, 0.4, -0.3]])
    d = make_rhs(net, laser)(0.0, y)
    assert abs(np.dot(y[6:], d[6:])) < 1e-15


@pytest.mark.parametrize("kw", [{"gamma": 0}, {"a": -1}, {"A": -1}, {"B": -2}])
def test_bad_lasers_are_refused(kw):
    with pytest.raises(ValueError):
        Laser(**kw)
