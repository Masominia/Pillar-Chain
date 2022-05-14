# Fixed-step integration, kicks and the detection of spikes.

"A kick adds amplitude * exp(i phase) to the field of one site at one time. The phase is in degrees."
struct Kick
    site::Int
    time::Float64
    amplitude::Float64
    phase::Float64
end

Kick(site, time, amplitude) = Kick(site, time, amplitude, 0.0)

"Spikes of every site as (time, peak intensity)."
struct Result
    sites::Int
    duration::Float64
    spikes::Vector{Vector{Tuple{Float64,Float64}}}
end

arrival(r::Result, site::Integer) = isempty(r.spikes[site]) ? nothing : r.spikes[site][1][1]
spike_count(r::Result, site::Integer) = length(r.spikes[site])
total_spikes(r::Result) = sum(length, r.spikes)

function last_spike(r::Result)
    latest = nothing
    for found in r.spikes, (t, _) in found
        (latest === nothing || t > latest) && (latest = t)
    end
    return latest
end

"One step of the classical fourth-order Runge-Kutta scheme."
function rk4_step(y, h, coupling, pump, laser)
    k1 = rhs(y, coupling, pump, laser)
    k2 = rhs(y .+ (0.5 * h) .* k1, coupling, pump, laser)
    k3 = rhs(y .+ (0.5 * h) .* k2, coupling, pump, laser)
    k4 = rhs(y .+ h .* k3, coupling, pump, laser)
    return y .+ (h / 6) .* (k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4)
end

function apply_kicks!(y, kicks, time, n)
    for k in kicks
        k.time == time && (y[2n + k.site] += k.amplitude * cis(deg2rad(k.phase)))
    end
    return y
end

function edges_of(kicks, duration)
    return sort(unique(vcat(Float64[k.time for k in kicks if k.time < duration], [0.0, Float64(duration)])))
end

"""
    simulate(network, laser, kicks, duration; threshold = 5.0, step = 0.02)

Integrates from rest. A spike is a maximum of the intensity of a site above `threshold`; its time and height
come from the parabola through the three samples around it.
"""
function simulate(net::Network, laser::Laser, kicks::Vector{Kick}, duration::Real; threshold::Real = 5.0, step::Real = 0.02)
    duration > 0 || throw(ArgumentError("the duration must be positive"))
    for k in kicks
        check_site(net, k.site)
    end
    n = net.sites
    coupling = coupling_matrix(net)
    pump = pump_vector(net, laser)
    y = rest_state(net, laser)
    spikes = [Tuple{Float64,Float64}[] for _ in 1:n]
    edges = edges_of(kicks, duration)
    for segment in 1:(length(edges) - 1)
        t0, t1 = edges[segment], edges[segment + 1]
        apply_kicks!(y, kicks, t0, n)
        count = max(round(Int, (t1 - t0) / step), 1)
        h = (t1 - t0) / count
        before = fill(NaN, n)
        here = abs2.(y[(2n + 1):(3n)])
        for i in 1:count
            y = rk4_step(y, h, coupling, pump, laser)
            after = abs2.(y[(2n + 1):(3n)])
            for site in 1:n
                if here[site] > before[site] && here[site] >= after[site] && here[site] >= 0.9 * threshold
                    bend = before[site] - 2 * here[site] + after[site]
                    shift = 0.5 * (before[site] - after[site]) / bend
                    peak = here[site] - 0.25 * (before[site] - after[site]) * shift
                    peak >= threshold && push!(spikes[site], (t0 + (i - 1 + shift) * h, peak))
                end
            end
            before, here = here, after
        end
    end
    return Result(n, Float64(duration), spikes)
end

"Intensity of every site at one time, by integrating from rest up to that time."
function intensity_at(net::Network, laser::Laser, kicks::Vector{Kick}, time::Real; step::Real = 0.02)
    time >= 0 || throw(ArgumentError("the time cannot be negative"))
    n = net.sites
    coupling = coupling_matrix(net)
    pump = pump_vector(net, laser)
    y = rest_state(net, laser)
    edges = sort(unique(vcat(Float64[k.time for k in kicks if k.time < time], [0.0, Float64(time)])))
    for segment in 1:(length(edges) - 1)
        t0, t1 = edges[segment], edges[segment + 1]
        apply_kicks!(y, kicks, t0, n)
        count = max(round(Int, (t1 - t0) / step), 1)
        h = (t1 - t0) / count
        for _ in 1:count
            y = rk4_step(y, h, coupling, pump, laser)
        end
    end
    time == 0 && apply_kicks!(y, kicks, 0.0, n)
    return abs2.(y[(2n + 1):(3n)])
end

"""
Intensities while every site is dark: with gain and absorption at rest the fields obey dE/dt = M E with
M = diag((1 - i alpha)(A_j - B - 1) / 2) + i K, solved by diagonalising M. For kicks too weak to bleach anything.
"""
function dark_intensities(net::Network, laser::Laser, kicks::Vector{Kick}, time::Real)
    n = net.sites
    pump = pump_vector(net, laser)
    m = Matrix(Diagonal((0.5 * (1 - im * laser.alpha)) .* (pump .- laser.B .- 1.0))) .+ im .* coupling_matrix(net)
    decomposition = eigen(m)
    field = zeros(ComplexF64, n)
    for k in kicks
        k.time <= time || continue
        start = zeros(ComplexF64, n)
        start[k.site] = k.amplitude * cis(deg2rad(k.phase))
        weights = decomposition.vectors \ start
        field .+= decomposition.vectors * (exp.(decomposition.values .* (time - k.time)) .* weights)
    end
    return abs2.(field)
end
