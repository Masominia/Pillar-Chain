# Lasers, networks and the equations of motion.

"Pump A, unsaturated absorption B, saturation ratio a, carrier rate gamma, linewidth factor alpha."
struct Laser
    A::Float64
    B::Float64
    a::Float64
    gamma::Float64
    alpha::Float64
    function Laser(A, B, a, gamma, alpha)
        (A >= 0 && B >= 0 && a > 0 && gamma > 0) ||
            throw(ArgumentError("the laser needs A >= 0, B >= 0, a > 0 and gamma > 0"))
        return new(A, B, a, gamma, alpha)
    end
end

Laser(; A = 6.5, B = 5.8, a = 1.8, gamma = 0.01, alpha = 2.0) = Laser(A, B, a, gamma, alpha)

"Sites numbered from 1, symmetric links with their coupling rates, and pumps that differ from the laser's."
mutable struct Network
    sites::Int
    links::Dict{Tuple{Int,Int},Float64}
    pumps::Dict{Int,Float64}
end

Network() = Network(0, Dict{Tuple{Int,Int},Float64}(), Dict{Int,Float64}())

function check_site(net::Network, site::Integer)
    1 <= site <= net.sites || throw(ArgumentError("site $site does not exist (there are $(net.sites))"))
    return nothing
end

function add_sites!(net::Network, count::Integer)
    count >= 1 || throw(ArgumentError("the number of sites must be positive"))
    net.sites += count
    return net
end

function link!(net::Network, i::Integer, j::Integer, kappa::Real)
    check_site(net, i)
    check_site(net, j)
    i != j || throw(ArgumentError("a site cannot be linked to itself"))
    kappa >= 0 || throw(ArgumentError("a coupling rate cannot be negative"))
    net.links[(min(i, j), max(i, j))] = kappa
    return net
end

function path!(net::Network, first::Integer, last::Integer, kappa::Real)
    last > first || throw(ArgumentError("a path needs its first site below its last"))
    for i in first:(last - 1)
        link!(net, i, i + 1, kappa)
    end
    return net
end

"Adds nx * ny sites, row by row, with links between nearest neighbours."
function grid!(net::Network, nx::Integer, ny::Integer, kappa::Real)
    (nx >= 1 && ny >= 1) || throw(ArgumentError("a grid needs positive sizes"))
    base = net.sites
    add_sites!(net, nx * ny)
    for iy in 0:(ny - 1), ix in 0:(nx - 1)
        me = base + iy * nx + ix + 1
        ix + 1 < nx && link!(net, me, me + 1, kappa)
        iy + 1 < ny && link!(net, me, me + nx, kappa)
    end
    return net
end

function set_pump!(net::Network, site::Integer, pump::Real)
    check_site(net, site)
    pump >= 0 || throw(ArgumentError("a pump cannot be negative"))
    net.pumps[site] = pump
    return net
end

function coupling_matrix(net::Network)
    m = zeros(net.sites, net.sites)
    for ((i, j), kappa) in net.links
        m[i, j] = kappa
        m[j, i] = kappa
    end
    return m
end

function pump_vector(net::Network, laser::Laser)
    pump = fill(laser.A, net.sites)
    for (site, value) in net.pumps
        pump[site] = value
    end
    return pump
end

function neighbours(net::Network, site::Integer)
    out = Int[]
    for (i, j) in keys(net.links)
        i == site && push!(out, j)
        j == site && push!(out, i)
    end
    return sort(out)
end

"""
The state is one complex vector of length 3n: gains, absorptions (both real) and fields.

    dE/dt = (1 - i alpha)(G - Q - 1) E / 2 + i K E
    dG/dt = gamma (A - G - G |E|^2)
    dQ/dt = gamma (B - Q - a Q |E|^2)
"""
function rhs(y::Vector{ComplexF64}, coupling::Matrix{Float64}, pump::Vector{Float64}, laser::Laser)
    n = length(pump)
    gain = real.(y[1:n])
    absorption = real.(y[(n + 1):(2n)])
    field = y[(2n + 1):(3n)]
    intensity = abs2.(field)
    d_gain = laser.gamma .* (pump .- gain .- gain .* intensity)
    d_absorption = laser.gamma .* (laser.B .- absorption .- laser.a .* absorption .* intensity)
    d_field = (0.5 * (1 - im * laser.alpha)) .* (gain .- absorption .- 1.0) .* field .+ im .* (coupling * field)
    return vcat(complex.(d_gain), complex.(d_absorption), d_field)
end

"All sites dark with gain and absorption relaxed."
function rest_state(net::Network, laser::Laser)
    n = net.sites
    return vcat(complex.(pump_vector(net, laser)), fill(complex(laser.B), n), zeros(ComplexF64, n))
end
