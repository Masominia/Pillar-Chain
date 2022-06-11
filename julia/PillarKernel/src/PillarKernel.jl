"""
A Julia kernel for the networks of the Python package: the same equations with complex fields, integrated by a
fixed-step fourth-order Runge-Kutta scheme. It reads the same network files and checks their expectations.
"""
module PillarKernel

using LinearAlgebra

export Laser, Network, add_sites!, link!, path!, grid!, set_pump!, coupling_matrix, pump_vector, neighbours
export Kick, Result, simulate, arrival, spike_count, total_spikes, last_spike, intensity_at, dark_intensities
export Case, parse_case, load_case, run_case, check_case, CheckResult

include("model.jl")
include("simulate.jl")
include("casefile.jl")
include("expect.jl")

end
