using Test
using PillarKernel

const CASES = normpath(joinpath(@__DIR__, "..", "..", "..", "cases"))

function chain(n, kappa)
    net = Network()
    add_sites!(net, n)
    path!(net, 1, n, kappa)
    return net
end

function single()
    net = Network()
    add_sites!(net, 1)
    return net
end

@testset "networks" begin
    net = chain(4, 0.06)
    @test net.sites == 4
    @test length(net.links) == 3
    @test neighbours(net, 2) == [1, 3]
    m = coupling_matrix(net)
    @test m == m'
    @test m[1, 2] == 0.06
    @test m[1, 3] == 0.0
    grid = Network()
    grid!(grid, 4, 3, 0.05)
    @test grid.sites == 12
    @test length(grid.links) == 17
    @test neighbours(grid, 6) == [2, 5, 7, 10]
    set_pump!(net, 2, 6.0)
    @test pump_vector(net, Laser()) == [6.5, 6.0, 6.5, 6.5]
    @test_throws ArgumentError link!(net, 1, 1, 0.1)
    @test_throws ArgumentError link!(net, 1, 9, 0.1)
    @test_throws ArgumentError link!(net, 1, 2, -0.1)
    @test_throws ArgumentError path!(net, 3, 2, 0.1)
    @test_throws ArgumentError set_pump!(net, 7, 6.0)
    @test_throws ArgumentError Laser(gamma = 0.0)
end

@testset "equations" begin
    net, laser = chain(3, 0.2), Laser()
    rest = PillarKernel.rest_state(net, laser)
    @test maximum(abs.(PillarKernel.rhs(rest, coupling_matrix(net), pump_vector(net, laser), laser))) == 0
    # with gain and loss balanced the coupling alone moves light without creating it
    y = ComplexF64[7.8, 7.8, 7.8, 6.8, 6.8, 6.8, 0.3 + 0.05im, -0.1 + 0.4im, 0.2 - 0.3im]
    d = PillarKernel.rhs(y, coupling_matrix(net), pump_vector(net, laser), laser)
    @test abs(sum(real.(conj.(y[7:9]) .* d[7:9]))) < 1e-15
end

@testset "one pillar" begin
    @test total_spikes(simulate(single(), Laser(), [Kick(1, 0.0, 1.2)], 400.0)) == 0
    r = simulate(single(), Laser(), [Kick(1, 0.0, 2.0)], 400.0)
    @test total_spikes(r) == 1
    @test isapprox(arrival(r, 1), 12.5825; atol = 2e-3)
    @test isapprox(r.spikes[1][1][2], 58.75; atol = 0.02)
    # two kicks of opposite phase cancel
    @test total_spikes(simulate(single(), Laser(), [Kick(1, 0.0, 2.0), Kick(1, 0.0, 2.0, 180.0)], 300.0)) == 0
    @test simulate(single(), Laser(), Kick[], 50.0).spikes == [Tuple{Float64,Float64}[]]
    @test last_spike(simulate(single(), Laser(), Kick[], 50.0)) === nothing
end

@testset "chains" begin
    r = simulate(chain(6, 0.06), Laser(), [Kick(1, 0.0, 2.0)], 600.0)
    times = [arrival(r, s) for s in 1:6]
    @test total_spikes(r) == 6
    @test issorted(times)
    weak = simulate(chain(6, 0.03), Laser(), [Kick(1, 0.0, 2.0)], 1500.0)
    @test spike_count(weak, 1) == 1
    @test total_spikes(weak) == 1
    # the mirror image of a chain gives the mirror image of the spikes
    mirror = simulate(chain(6, 0.06), Laser(), [Kick(6, 0.0, 2.0)], 600.0)
    @test isapprox([arrival(mirror, s) for s in 6:-1:1], times; atol = 1e-8)
    # halving the step changes the arrival times very little
    fine = simulate(chain(6, 0.06), Laser(), [Kick(1, 0.0, 2.0)], 600.0; step = 0.01)
    @test isapprox([arrival(fine, s) for s in 1:6], times; atol = 1e-4)
end

@testset "dark regime" begin
    net = Network()
    add_sites!(net, 2)
    link!(net, 1, 2, 0.2)
    kicks = [Kick(1, 0.0, 0.001)]
    for t in (1.0, 4.0, 9.0)
        decay = 1e-6 * exp((6.5 - 5.8 - 1) * t)
        exact = dark_intensities(net, Laser(), kicks, t)
        @test isapprox(exact[1], decay * cos(0.2 * t)^2; rtol = 1e-10)
        @test isapprox(exact[2], decay * sin(0.2 * t)^2; rtol = 1e-10)
        @test isapprox(intensity_at(net, Laser(), kicks, t), exact; rtol = 1e-4)
    end
    @test intensity_at(net, Laser(), kicks, 0.0) ≈ [1e-6, 0.0]
end

@testset "network files" begin
    case = parse_case("title Two arms\nlaser gamma=0.02\nsites 4\npath 1 4 kappa=0.06 # note\npump 2 3 A=6.2\nkick 3 time=40 amplitude=1.5 phase=90\nrun 500\nexpect total 4\n")
    @test case.title == "Two arms"
    @test case.laser.gamma == 0.02
    @test case.laser.A == 6.5
    @test case.network.sites == 4
    @test case.network.pumps == Dict(2 => 6.2, 3 => 6.2)
    @test case.kicks[1].time == 40.0
    @test case.kicks[1].phase == 90.0
    @test case.duration == 500.0
    @test case.expectations[1].line == 8
    @test_throws ArgumentError parse_case("sites 2\nlink 1 2\nrun 10")
    @test_throws ArgumentError parse_case("sites 2\nwire 1 2\nrun 10")
    @test_throws ArgumentError parse_case("sites two\nrun 10")
    @test_throws ArgumentError parse_case("run 10")
    @test_throws ArgumentError parse_case("sites 2")
    @test_throws ArgumentError parse_case("sites 2\nkick 5 amplitude=1\nrun 10")
    message = try
        parse_case("sites 2\nlink 1 3 kappa=0.1\nrun 10")
        ""
    catch err
        err.msg
    end
    @test occursin("line 2", message)
end

@testset "expectations" begin
    case = parse_case("sites 1\nkick 1 amplitude=2\nrun 200\nexpect total 1\nexpect total 3\nexpect colour 1 red\nexpect arrival 1 soon 1\n")
    checks = check_case(case)
    @test [c.passed for c in checks] == [true, false, false, false]
    @test occursin("line 6", checks[3].detail)
    @test occursin("line 7", checks[4].detail)
end

# A part of the library shared with the Python package: every expectation in these files must hold here too.
const LIBRARY = [
    "chain_strong015_kick2",
    "collision_antiphase",
    "collision_even",
    "collision_odd",
    "collision_offset",
    "collision_three",
    "junction_and_antiphase",
    "junction_and_both",
    "junction_and_first",
    "junction_and_offset02",
    "junction_and_offset05",
    "junction_and_offset10",
    "junction_and_offset40",
    "junction_and_quadrature",
    "junction_and_second",
    "junction_or_one",
    "junction_xor",
    "linear_chain3",
    "linear_grid3",
    "linear_pair_alpha0",
    "linear_pair_alpha5",
    "linear_pair_detuned",
    "linear_pair_k005",
    "linear_pair_k020",
    "linear_ring4",
    "ring_single_n12",
    "single_kick10",
    "single_kick12",
    "single_kick14",
    "single_kick16",
    "single_kick20",
    "single_kick30",
    "single_refractory_dt160",
    "single_sum_dt020",
]

@testset "library: $name" for name in LIBRARY
    checks = check_case(load_case(joinpath(CASES, name * ".pil")))
    @test !isempty(checks)
    for c in checks
        c.passed || @info "failed: $name: $(c.name): $(c.detail)"
        @test c.passed
    end
end
