# Network files

A network file (`.pil`) describes a set of coupled pillars, the kicks that excite it, how long to simulate and what must come out. One statement per line; `#` starts a comment. Times are in photon lifetimes, rates per photon lifetime, phases in degrees.

## Statements

| Statement | Meaning |
|---|---|
| `title <text>` | a title for reports |
| `laser [A=] [B=] [a=] [gamma=] [alpha=]` | the laser of every pillar; anything not given keeps its default (6.5, 5.8, 1.8, 0.01, 2) |
| `sites <n>` | adds n pillars, numbered on from the last |
| `link <i> <j> kappa=<rate>` | couples two pillars; a second link between the same pair replaces the first |
| `path <i> <j> kappa=<rate>` | links i to i+1, ..., j-1 to j |
| `grid <nx> <ny> kappa=<rate>` | adds nx * ny pillars, row by row, with nearest-neighbour links |
| `pump <i> [<j>] A=<pump>` | gives one pillar, or the range i to j, its own pump |
| `kick <i> amplitude=<a> [time=<t>] [phase=<degrees>]` | adds a * exp(i phase) to the field of pillar i at time t (default 0) |
| `run <duration>` | how long to simulate, from rest |
| `threshold <intensity>` | a maximum of the intensity above this counts as a spike (default 5) |
| `expect <kind> ...` | something the result must satisfy |

A file needs at least one pillar and a `run`. Kicks must name existing pillars and lie inside the run.

Pillars added by `grid` are numbered row by row: with `grid 6 6`, pillar 8 is the second of the second row. A `grid` after `sites 5` starts at pillar 6.

## Expectations

| Expectation | Holds when |
|---|---|
| `fired <i> yes\|no` | pillar i spiked at least once, or never |
| `count <i> <n>` | pillar i spiked exactly n times |
| `each <i> <j> <n>` | every pillar from i to j spiked exactly n times |
| `silent <i> <j>` | no pillar from i to j spiked |
| `total <n>` | the whole network spiked n times |
| `arrival <i> <t> <tolerance>` | the first spike of pillar i is within the tolerance of t |
| `peak <i> <I> <relative tolerance>` | the height of that spike |
| `delay <i> <j> <t> <tolerance>` | first spike of j minus first spike of i |
| `order <i> <j> ...` | the first spikes come in this order |
| `together <i> <j> <tolerance>` | the first spikes of i and j coincide within the tolerance |
| `last <t> <tolerance>` | the time of the last spike anywhere |
| `quiet_after <t>` | nothing spikes after t |
| `intensity <i> <t> <I> <relative tolerance>` | the intensity of pillar i at time t |

A malformed expectation (unknown kind, wrong number of arguments, a pillar that does not exist or never spiked where a time is needed) is reported as a failed check with its line number; the other expectations are still evaluated.

## Errors

A file that cannot be read as a network is refused with the line number and the reason, for example `line 4: link needs kappa=...` or `line 7: site 9 does not exist (there are 8)`. `python -m pillarchain check` then exits with status 2; with status 1 if the file is read but an expectation fails; with 0 otherwise.

## Example

```
# Two pulses launched from the ends of a chain meet in the middle and annihilate.
title Collision in a chain of 15
sites 15
path 1 15 kappa=0.06
kick 1 amplitude=2
kick 15 amplitude=2
run 1200
expect each 1 15 1
expect together 7 9 1e-6
expect quiet_after 130
```
