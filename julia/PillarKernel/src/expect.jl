# The expectations of a network file, evaluated on a result.

struct CheckResult
    name::String
    passed::Bool
    detail::String
end

function arity(e::Expectation, count::Integer)
    length(e.args) == count || throw(ArgumentError("'$(e.kind)' takes $count argument$(count == 1 ? "" : "s")"))
    return nothing
end

function site_arg(e::Expectation, i::Integer, r::Result)
    value = number_of(e.args[i])
    (value == floor(value) && 1 <= value <= r.sites) || throw(ArgumentError("site $(e.args[i]) does not exist"))
    return Int(value)
end

function arrival_of(r::Result, site::Integer)
    t = arrival(r, site)
    t === nothing && throw(ArgumentError("site $site never spiked"))
    return t
end

function range_arg(e::Expectation, r::Result)
    from, to = site_arg(e, 1, r), site_arg(e, 2, r)
    to >= from || throw(ArgumentError("a range needs its first site below its last"))
    return from:to
end

function check_one(case::Case, r::Result, e::Expectation, step::Real)
    k = e.kind
    num(i) = number_of(e.args[i])
    if k == "fired"
        arity(e, 2)
        e.args[2] in ("yes", "no") || throw(ArgumentError("'fired' takes a site and yes or no"))
        n = spike_count(r, site_arg(e, 1, r))
        return (n > 0) == (e.args[2] == "yes"), "$n spike(s)"
    elseif k == "count"
        arity(e, 2)
        n = spike_count(r, site_arg(e, 1, r))
        return n == num(2), "$n spike(s)"
    elseif k == "each" || k == "silent"
        arity(e, k == "each" ? 3 : 2)
        want = k == "each" ? num(3) : 0.0
        odd = ["site $s: $(spike_count(r, s))" for s in range_arg(e, r) if spike_count(r, s) != want]
        return isempty(odd), isempty(odd) ? "all as expected" : join(odd[1:min(end, 6)], ", ")
    elseif k == "total"
        arity(e, 1)
        return total_spikes(r) == num(1), "$(total_spikes(r)) spike(s)"
    elseif k == "arrival"
        arity(e, 3)
        t = arrival_of(r, site_arg(e, 1, r))
        return abs(t - num(2)) <= num(3), "$t, expected $(num(2))"
    elseif k == "peak"
        arity(e, 3)
        site = site_arg(e, 1, r)
        arrival_of(r, site)
        peak = r.spikes[site][1][2]
        return abs(peak / num(2) - 1) <= num(3), "$peak, expected $(num(2))"
    elseif k == "delay"
        arity(e, 4)
        d = arrival_of(r, site_arg(e, 2, r)) - arrival_of(r, site_arg(e, 1, r))
        return abs(d - num(3)) <= num(4), "$d, expected $(num(3))"
    elseif k == "order"
        length(e.args) >= 2 || throw(ArgumentError("'order' takes at least two sites"))
        times = [arrival_of(r, site_arg(e, i, r)) for i in 1:length(e.args)]
        return all(diff(times) .> 0), join(times, ", ")
    elseif k == "together"
        arity(e, 3)
        d = arrival_of(r, site_arg(e, 2, r)) - arrival_of(r, site_arg(e, 1, r))
        return abs(d) <= num(3), "apart by $d"
    elseif k == "last"
        arity(e, 2)
        late = last_spike(r)
        late === nothing && throw(ArgumentError("nothing spiked"))
        return abs(late - num(1)) <= num(2), "$late, expected $(num(1))"
    elseif k == "quiet_after"
        arity(e, 1)
        late = last_spike(r)
        return late === nothing || late <= num(1), late === nothing ? "nothing spiked" : "last spike at $late"
    elseif k == "intensity"
        arity(e, 4)
        site, t = site_arg(e, 1, r), num(2)
        0 <= t <= r.duration || throw(ArgumentError("time $t lies outside the run"))
        got = intensity_at(case.network, case.laser, case.kicks, t; step = step)[site]
        return abs(got / num(3) - 1) <= num(4), "$got, expected $(num(3))"
    end
    throw(ArgumentError("unknown expectation '$k'"))
end

"""
    check_case(case; step = 0.02)

Simulates the case and evaluates its expectations. A malformed expectation becomes a failed check with its line
number; it does not stop the others.
"""
function check_case(case::Case; step::Real = 0.02)
    r = run_case(case; step = step)
    out = CheckResult[]
    for e in case.expectations
        name = join(vcat([e.kind], e.args), " ")
        try
            passed, detail = check_one(case, r, e, step)
            push!(out, CheckResult(name, passed, detail))
        catch err
            err isa ArgumentError || rethrow()
            push!(out, CheckResult(name, false, "line $(e.line): $(err.msg)"))
        end
    end
    return out
end
