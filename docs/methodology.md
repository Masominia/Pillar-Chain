# Methodology

## Model

Each pillar is a single-mode laser with a saturable absorber, described by the Yamada equations with a complex field, in units of the photon lifetime:

    dE_j/dt = (1 - i alpha) (G_j - Q_j - 1) E_j / 2 + i sum_k kappa_jk E_k
    dG_j/dt = gamma (A_j - G_j - G_j |E_j|^2)
    dQ_j/dt = gamma (B - Q_j - a Q_j |E_j|^2)

G is the gain, Q the absorption, A the pump, B the unsaturated absorption, a the ratio of the saturation of absorber and gain, gamma the carrier relaxation rate, alpha the linewidth enhancement factor. The coupling is conservative (evanescent overlap of neighbouring modes): a real, symmetric rate kappa_jk multiplied by i, so that light moves between cavities without being created. All pillars have the same resonance frequency.

The default laser (A = 6.5, B = 5.8, a = 1.8, gamma = 0.01, alpha = 2) is excitable: its lasing threshold is A = 1 + B = 6.8, and below it the dark state is stable but a strong enough perturbation triggers one pulse.

A kick adds a complex amplitude to the field of one pillar instantaneously. It stands for a short optical perturbation resonant with the mode. There is no noise and no spontaneous emission: a pillar that is not kicked or fed by a neighbour stays exactly dark.

## Integration

The state (G, Q, Re E, Im E) is integrated from rest by an explicit Runge-Kutta scheme of order eight (DOP853) with relative tolerance 1e-9 and absolute tolerance 1e-12, piecewise between kicks, with dense output.

A spike is a maximum of the intensity of one pillar above a threshold (5 by default; a full pulse peaks near 57). Maxima are located as roots of d|E|^2/dt on the dense solution, bracketed between solver steps and refined by Brent's method, so spike times do not depend on a sampling grid.

## Independent integration

`reference.py` writes the equations a second time with complex arithmetic and integrates them with a different method (LSODA, tolerances 1e-10 and 1e-13). Spikes are found there by sampling the dense solution every 0.05 and fitting a parabola through each maximum. `compare.py` requires the same number of spikes on every pillar, times within 5e-3 and heights within 2e-4 relative. Before the first spike it also compares the intensities on a logarithmic scale, where they span many decades.

Two further references:

- **Dark regime.** For kicks too weak to bleach anything the fields obey linear equations with constant coefficients, dE/dt = M E with M = diag((1 - i alpha)(A_j - B - 1) / 2) + i K. The `linear_` cases are checked against the solution by diagonalisation of M; for two identical cavities this is the textbook beating, cos^2 and sin^2 of kappa t under a common decay.
- **Fixed step.** A classical fourth-order Runge-Kutta integration with a fixed step must converge to the adaptive one at fourth order. The Julia kernel uses this scheme.

Two symmetries of the equations are checked exactly: a common phase on all kicks changes nothing, and the mirror image of a chain gives the mirror image of its spikes.

## Where expectations come from

The numerical expectations in the case files (total number of spikes, time of the last one, and count, arrival time and height on up to ten pillars) were produced by the independent integration, not by the package. The physical expectations (which pillars fire, in what order, which fire together) are written by hand from what the case is meant to show.

## Studies

- **Speed.** Delay per site between one third and two thirds of a chain of 12, against the coupling.
- **Critical coupling.** Bisection on "the pulse reaches the end of a chain of 6" to 2e-5, for a given kick. It is repeated against the pump and against the kick amplitude.
- **Refractory time.** Bisection on the delay after which a second identical kick fires a single pillar again, assuming one switch between 20 and 600 photon lifetimes.
- **Rings.** A pulse is left circulating in rings of several sizes by a second kick in the vulnerable window. The round trip is the last interval between spikes of pillar 1 in a run of 5000 photon lifetimes, compared with the number of sites times the delay per site of an open chain; the change over the last round trip is reported as a measure of settling.
- **Junctions.** The output arm of every junction case read as a truth table.

## Julia kernel

`julia/PillarKernel` holds the same equations with complex vectors, a fixed-step fourth-order Runge-Kutta integrator (step 0.02), spike detection by a parabola through three samples, the closed form of the dark regime, and a reader for the same network files with all thirteen kinds of expectation. Its tests include a part of the library. Its algorithm was mirrored in Python to choose that part; the Julia tests themselves run in the CI workflow (`make julia-test` locally).
