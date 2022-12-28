# PillarChain report

94 networks, 993 pillars, 1105 spikes, 2146 checks: 2146 PASS, 0 FAIL.

Every network is a text file in `cases/`. Its expectations come from an independent integration or a closed form, stated in the comments at the top of the file.
Per-case results are in `reports/cases/`, figures in `reports/figures/cases/`. Times are in photon lifetimes.

## Families

| family | cases | sites | spikes | checks | passed |
|---|---|---|---|---|---|
| chains | 26 | 242 | 226 | 633 | 633 |
| collisions | 5 | 82 | 81 | 169 | 169 |
| defects | 8 | 72 | 52 | 204 | 204 |
| diode | 3 | 51 | 39 | 42 | 42 |
| lattices | 5 | 176 | 154 | 120 | 120 |
| junctions | 13 | 208 | 162 | 376 | 376 |
| dark regime | 8 | 26 | 0 | 79 | 79 |
| rings | 6 | 81 | 248 | 196 | 196 |
| single pillar | 15 | 15 | 14 | 81 | 81 |
| pulse trains | 5 | 40 | 129 | 140 | 140 |

## Agreement with the independent integration

Spike times are absolute differences in photon lifetimes, peaks relative, dark intensities differences of the logarithm before the first spike.

| quantity | largest difference over the library |
|---|---|
| spike time | 3.21e-03 |
| spike peak | 6.63e-06 |
| dark intensity | 8.46e-07 |

## Studies

### Pulse speed against coupling (chain of 12, measured between sites 4 and 8)

Critical coupling for a kick of amplitude 2, by bisection: 0.04186.

| coupling | delay per site | peak | delay times coupling |
|---|---|---|---|
| 0.0420 | 86.8466 | 54.9934 | 3.6476 |
| 0.0440 | 44.7739 | 55.5240 | 1.9701 |
| 0.0460 | 35.2149 | 55.7308 | 1.6199 |
| 0.0500 | 26.6334 | 56.0208 | 1.3317 |
| 0.0550 | 20.6419 | 56.3707 | 1.1353 |
| 0.0600 | 17.2357 | 56.7097 | 1.0341 |
| 0.0700 | 13.9940 | 57.1752 | 0.9796 |
| 0.0800 | 12.1662 | 57.8404 | 0.9733 |
| 0.0900 | 10.7291 | 58.6622 | 0.9656 |
| 0.1000 | 9.4225 | 59.3036 | 0.9422 |
| 0.1200 | 7.1285 | 58.3631 | 0.8554 |

### Critical coupling against the pump (kick of amplitude 2.5)

| pump | distance below threshold | critical coupling |
|---|---|---|
| 6.4000 | 0.4000 | 0.0584 |
| 6.4500 | 0.3500 | 0.0506 |
| 6.5000 | 0.3000 | 0.0440 |
| 6.5500 | 0.2500 | 0.0369 |
| 6.6000 | 0.2000 | 0.0293 |
| 6.6500 | 0.1500 | 0.0216 |
| 6.7000 | 0.1000 | 0.0148 |

### Critical coupling against the launching kick

The threshold depends on how the pulse is launched: it moves by 0.0021 over these kicks. It is not monotonic in the kick.

| kick | critical coupling |
|---|---|
| 1.6000 | 0.0418 |
| 2.0000 | 0.0419 |
| 2.5000 | 0.0440 |
| 3.0000 | 0.0436 |
| 4.0000 | 0.0418 |

### Refractory time of one pillar against the kick

Shortest delay after which a second kick of the same amplitude fires the pillar again, by bisection between 20 and 600.

| kick | refractory time |
|---|---|
| 1.600 | 204.507 |
| 2.000 | 140.503 |
| 2.500 | 105.669 |
| 3.000 | 88.110 |
| 4.000 | 91.792 |
| 6.000 | 94.058 |

### Pulses held in rings

Coupling 0.06, second kick on the last site at t = 185. Delay per site of an open chain at the same coupling: 17.236.

| sites | round trips | round trip | settling | per site | over open chain |
|---|---|---|---|---|---|
| 10 | 19 | 253.1622 | 1.81e-05 | 25.3162 | 1.4688 |
| 12 | 18 | 276.7151 | 5.34e-07 | 23.0596 | 1.3379 |
| 16 | 15 | 325.2811 | 1.38e-08 | 20.3301 | 1.1795 |
| 20 | 13 | 377.8132 | 8.92e-09 | 18.8907 | 1.0960 |
| 30 | 9 | 527.0653 | 1.91e-08 | 17.5688 | 1.0193 |

### What comes out of the junctions

Phase and lag of the second input relative to the first; output read at the end of the output arm.

| case | input 1 | input 2 | phase | lag | output | at |
|---|---|---|---|---|---|---|
| junction_and_antiphase | yes | yes | 180.00 | 0.00 | no | n/a |
| junction_and_both | yes | yes | 0.00 | 0.00 | yes | 184.15 |
| junction_and_first | yes | no | n/a | n/a | no | n/a |
| junction_and_offset02 | yes | yes | 0.00 | 2.00 | yes | 187.18 |
| junction_and_offset05 | yes | yes | 0.00 | 5.00 | yes | 206.56 |
| junction_and_offset10 | yes | yes | 0.00 | 10.00 | no | n/a |
| junction_and_offset40 | yes | yes | 0.00 | 40.00 | no | n/a |
| junction_and_quadrature | yes | yes | 90.00 | 0.00 | yes | 215.47 |
| junction_and_second | no | yes | n/a | n/a | no | n/a |
| junction_or_both | yes | yes | 0.00 | 0.00 | yes | 176.02 |
| junction_or_one | yes | no | n/a | n/a | yes | 187.10 |
| junction_xor | yes | yes | 180.00 | 0.00 | no | n/a |

### Fixed-step integration against the adaptive solver (three sites, one pulse)

| step | difference | order |
|---|---|---|
| 0.2000 | 3.66e-06 | n/a |
| 0.1000 | 2.32e-07 | 3.9799 |
| 0.0500 | 1.46e-08 | 3.9892 |

## All networks

| case | sites | links | kicks | spikes | last spike | checks | passed |
|---|---|---|---|---|---|---|---|
| chain_alpha0 | 8 | 7 | 1 | 8 | 69.433 | 27 | 27 |
| chain_alpha1 | 8 | 7 | 1 | 8 | 90.946 | 27 | 27 |
| chain_alpha3 | 8 | 7 | 1 | 8 | 189.769 | 27 | 27 |
| chain_alpha5 | 8 | 7 | 1 | 1 | 12.757 | 13 | 13 |
| chain_gamma005 | 8 | 7 | 1 | 8 | 150.383 | 27 | 27 |
| chain_gamma020 | 8 | 7 | 1 | 8 | 130.471 | 27 | 27 |
| chain_kappa030 | 8 | 7 | 1 | 1 | 12.673 | 14 | 14 |
| chain_kappa040 | 8 | 7 | 1 | 1 | 12.746 | 14 | 14 |
| chain_kappa042 | 8 | 7 | 1 | 8 | 578.688 | 28 | 28 |
| chain_kappa045 | 8 | 7 | 1 | 8 | 282.203 | 28 | 28 |
| chain_kappa050 | 8 | 7 | 1 | 8 | 197.588 | 28 | 28 |
| chain_kappa060 | 8 | 7 | 1 | 8 | 133.277 | 28 | 28 |
| chain_kappa070 | 8 | 7 | 1 | 8 | 110.370 | 28 | 28 |
| chain_kappa080 | 8 | 7 | 1 | 8 | 97.670 | 28 | 28 |
| chain_kappa100 | 8 | 7 | 1 | 8 | 78.805 | 28 | 28 |
| chain_kappa120 | 8 | 7 | 1 | 8 | 63.801 | 28 | 28 |
| chain_long20 | 20 | 19 | 1 | 20 | 340.099 | 33 | 33 |
| chain_long30 | 30 | 29 | 1 | 30 | 512.450 | 33 | 33 |
| chain_pump620 | 8 | 7 | 1 | 1 | 34.606 | 13 | 13 |
| chain_pump635 | 8 | 7 | 1 | 1 | 13.023 | 13 | 13 |
| chain_pump665 | 8 | 7 | 1 | 8 | 93.006 | 27 | 27 |
| chain_pump675 | 8 | 7 | 1 | 8 | 72.153 | 27 | 27 |
| chain_strong015_kick2 | 8 | 7 | 1 | 15 | 52.410 | 26 | 26 |
| chain_strong020_kick4 | 8 | 7 | 1 | 15 | 30.817 | 26 | 26 |
| chain_strong040_kick2 | 8 | 7 | 1 | 0 | n/a | 9 | 9 |
| chain_strong040_kick4 | 8 | 7 | 1 | 21 | 19.870 | 26 | 26 |
| collision_antiphase | 15 | 14 | 2 | 14 | 116.042 | 32 | 32 |
| collision_even | 16 | 15 | 2 | 16 | 133.700 | 34 | 34 |
| collision_odd | 15 | 14 | 2 | 15 | 124.788 | 35 | 35 |
| collision_offset | 15 | 14 | 2 | 15 | 155.308 | 35 | 35 |
| collision_three | 21 | 20 | 3 | 21 | 90.711 | 33 | 33 |
| defect_link030 | 9 | 8 | 1 | 4 | 64.605 | 21 | 21 |
| defect_link042 | 9 | 8 | 1 | 4 | 64.863 | 21 | 21 |
| defect_link045 | 9 | 8 | 1 | 9 | 174.513 | 30 | 30 |
| defect_link050 | 9 | 8 | 1 | 9 | 159.837 | 30 | 30 |
| defect_pump500 | 9 | 8 | 1 | 4 | 64.462 | 21 | 21 |
| defect_pump630 | 9 | 8 | 1 | 4 | 64.905 | 21 | 21 |
| defect_pump640 | 9 | 8 | 1 | 9 | 180.986 | 30 | 30 |
| defect_pump670 | 9 | 8 | 1 | 9 | 145.682 | 30 | 30 |
| diode_backward | 17 | 22 | 3 | 17 | 384.962 | 15 | 15 |
| diode_forward | 17 | 22 | 1 | 5 | 231.342 | 12 | 12 |
| diode_open | 17 | 22 | 1 | 17 | 255.592 | 15 | 15 |
| grid_centre | 49 | 84 | 1 | 50 | 103.458 | 29 | 29 |
| grid_corner | 36 | 60 | 1 | 36 | 133.137 | 29 | 29 |
| grid_strip | 30 | 47 | 3 | 31 | 187.244 | 27 | 27 |
| grid_two_corners | 36 | 60 | 2 | 36 | 97.328 | 26 | 26 |
| grid_weak | 25 | 40 | 1 | 1 | 9.046 | 9 | 9 |
| junction_and_antiphase | 16 | 15 | 2 | 10 | 81.571 | 26 | 26 |
| junction_and_both | 16 | 15 | 2 | 16 | 184.145 | 33 | 33 |
| junction_and_first | 16 | 15 | 1 | 5 | 81.830 | 20 | 20 |
| junction_and_offset02 | 16 | 15 | 2 | 16 | 187.180 | 33 | 33 |
| junction_and_offset05 | 16 | 15 | 2 | 16 | 206.561 | 33 | 33 |
| junction_and_offset10 | 16 | 15 | 2 | 10 | 91.649 | 25 | 25 |
| junction_and_offset40 | 16 | 15 | 2 | 10 | 121.546 | 25 | 25 |
| junction_and_quadrature | 16 | 15 | 2 | 16 | 215.471 | 33 | 33 |
| junction_and_second | 16 | 15 | 1 | 5 | 81.830 | 21 | 21 |
| junction_fanout | 16 | 15 | 1 | 16 | 187.101 | 34 | 34 |
| junction_or_both | 16 | 15 | 2 | 16 | 176.022 | 33 | 33 |
| junction_or_one | 16 | 15 | 1 | 16 | 187.101 | 34 | 34 |
| junction_xor | 16 | 15 | 2 | 10 | 81.571 | 26 | 26 |
| linear_chain3 | 3 | 2 | 1 | 0 | n/a | 10 | 10 |
| linear_grid3 | 9 | 12 | 1 | 0 | n/a | 16 | 16 |
| linear_pair_alpha0 | 2 | 1 | 1 | 0 | n/a | 8 | 8 |
| linear_pair_alpha5 | 2 | 1 | 1 | 0 | n/a | 8 | 8 |
| linear_pair_detuned | 2 | 1 | 1 | 0 | n/a | 8 | 8 |
| linear_pair_k005 | 2 | 1 | 1 | 0 | n/a | 9 | 9 |
| linear_pair_k020 | 2 | 1 | 1 | 0 | n/a | 9 | 9 |
| linear_ring4 | 4 | 4 | 1 | 0 | n/a | 11 | 11 |
| ring_memory_n20 | 20 | 20 | 2 | 104 | 1,847.005 | 32 | 32 |
| ring_second_kick150 | 12 | 12 | 2 | 12 | 108.441 | 33 | 33 |
| ring_second_kick185 | 12 | 12 | 2 | 83 | 1,847.611 | 32 | 32 |
| ring_second_kick230 | 12 | 12 | 2 | 24 | 395.630 | 33 | 33 |
| ring_single_n12 | 12 | 12 | 1 | 12 | 108.441 | 33 | 33 |
| ring_single_n13 | 13 | 13 | 1 | 13 | 117.354 | 33 | 33 |
| single_kick10 | 1 | 0 | 1 | 0 | n/a | 3 | 3 |
| single_kick12 | 1 | 0 | 1 | 0 | n/a | 3 | 3 |
| single_kick14 | 1 | 0 | 1 | 1 | 28.982 | 6 | 6 |
| single_kick16 | 1 | 0 | 1 | 1 | 19.548 | 6 | 6 |
| single_kick20 | 1 | 0 | 1 | 1 | 12.583 | 6 | 6 |
| single_kick30 | 1 | 0 | 1 | 1 | 6.936 | 6 | 6 |
| single_phase | 1 | 0 | 1 | 1 | 12.583 | 6 | 6 |
| single_refractory_dt080 | 1 | 0 | 2 | 1 | 12.583 | 6 | 6 |
| single_refractory_dt140 | 1 | 0 | 2 | 1 | 12.583 | 6 | 6 |
| single_refractory_dt160 | 1 | 0 | 2 | 2 | 192.942 | 6 | 6 |
| single_refractory_dt300 | 1 | 0 | 2 | 2 | 314.499 | 6 | 6 |
| single_sum_dt005 | 1 | 0 | 2 | 1 | 24.812 | 6 | 6 |
| single_sum_dt020 | 1 | 0 | 2 | 1 | 63.995 | 6 | 6 |
| single_sum_dt050 | 1 | 0 | 2 | 1 | 89.479 | 6 | 6 |
| single_sum_dt100 | 1 | 0 | 2 | 0 | n/a | 3 | 3 |
| train_dt100 | 8 | 7 | 4 | 16 | 417.313 | 28 | 28 |
| train_dt150 | 8 | 7 | 4 | 17 | 497.690 | 28 | 28 |
| train_dt200 | 8 | 7 | 4 | 32 | 883.374 | 28 | 28 |
| train_dt300 | 8 | 7 | 4 | 32 | 1,064.122 | 28 | 28 |
| train_dt500 | 8 | 7 | 4 | 32 | 1,636.518 | 28 | 28 |
