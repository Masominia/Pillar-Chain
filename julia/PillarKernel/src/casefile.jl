# Reader for the network files shared with the Python package.

struct Expectation
    kind::String
    args::Vector{String}
    line::Int
end

struct Case
    title::String
    laser::Laser
    network::Network
    kicks::Vector{Kick}
    duration::Float64
    threshold::Float64
    expectations::Vector{Expectation}
end

function number_of(word::AbstractString)
    value = tryparse(Float64, word)
    value === nothing && throw(ArgumentError("'$word' is not a number"))
    return value
end

function site_of(value::Real)
    (value == floor(value) && value >= 1) || throw(ArgumentError("'$value' is not a site number"))
    return Int(value)
end

"Leading numbers and trailing key=value pairs of a statement."
function split_statement(words, allowed, owner::AbstractString)
    numbers = Float64[]
    pairs = Dict{String,Float64}()
    for w in words
        if occursin('=', w)
            parts = split(w, '='; limit = 2)
            String(parts[1]) in allowed || throw(ArgumentError("$owner does not have '$(parts[1])'"))
            pairs[String(parts[1])] = number_of(parts[2])
        else
            push!(numbers, number_of(w))
        end
    end
    return numbers, pairs
end

function need(pairs::Dict{String,Float64}, key::AbstractString, owner::AbstractString)
    haskey(pairs, key) || throw(ArgumentError("$owner needs $key=..."))
    return pairs[key]
end

function takes(numbers, count::Integer, owner::AbstractString)
    length(numbers) == count || throw(ArgumentError("$owner takes $count number$(count == 1 ? "" : "s") before its options"))
    return nothing
end

"Parses a case. Throws ArgumentError with the line number on any error."
function parse_case(text::AbstractString)
    title = ""
    laser = Laser()
    net = Network()
    kicks = Kick[]
    duration = 0.0
    threshold = 5.0
    expectations = Expectation[]
    for (number, raw) in enumerate(split(text, '\n'))
        line = strip(first(split(raw, '#'; limit = 2)))
        isempty(line) && continue
        words = split(line)
        key, rest = words[1], words[2:end]
        try
            if key == "expect"
                length(words) >= 2 || throw(ArgumentError("expect needs a kind"))
                push!(expectations, Expectation(String(words[2]), String.(words[3:end]), number))
            elseif key == "title"
                title = String(strip(line[6:end]))
            elseif key == "laser"
                numbers, pairs = split_statement(rest, ("A", "B", "a", "gamma", "alpha"), "laser")
                takes(numbers, 0, "laser")
                laser = Laser(
                    get(pairs, "A", laser.A),
                    get(pairs, "B", laser.B),
                    get(pairs, "a", laser.a),
                    get(pairs, "gamma", laser.gamma),
                    get(pairs, "alpha", laser.alpha),
                )
            elseif key == "sites"
                numbers, _ = split_statement(rest, (), "sites")
                takes(numbers, 1, "sites")
                add_sites!(net, site_of(numbers[1]))
            elseif key == "path" || key == "link"
                numbers, pairs = split_statement(rest, ("kappa",), key)
                takes(numbers, 2, key)
                build! = key == "path" ? path! : link!
                build!(net, site_of(numbers[1]), site_of(numbers[2]), need(pairs, "kappa", key))
            elseif key == "grid"
                numbers, pairs = split_statement(rest, ("kappa",), "grid")
                takes(numbers, 2, "grid")
                grid!(net, site_of(numbers[1]), site_of(numbers[2]), need(pairs, "kappa", "grid"))
            elseif key == "pump"
                numbers, pairs = split_statement(rest, ("A",), "pump")
                length(numbers) in (1, 2) || throw(ArgumentError("pump takes a site or a range of sites"))
                from, to = site_of(numbers[1]), site_of(numbers[end])
                to >= from || throw(ArgumentError("a range needs its first site below its last"))
                for site in from:to
                    set_pump!(net, site, need(pairs, "A", "pump"))
                end
            elseif key == "kick"
                numbers, pairs = split_statement(rest, ("time", "amplitude", "phase"), "kick")
                takes(numbers, 1, "kick")
                push!(kicks, Kick(site_of(numbers[1]), get(pairs, "time", 0.0), need(pairs, "amplitude", "kick"), get(pairs, "phase", 0.0)))
            elseif key == "run"
                numbers, _ = split_statement(rest, (), "run")
                takes(numbers, 1, "run")
                numbers[1] > 0 || throw(ArgumentError("the duration must be positive"))
                duration = numbers[1]
            elseif key == "threshold"
                numbers, _ = split_statement(rest, (), "threshold")
                takes(numbers, 1, "threshold")
                numbers[1] > 0 || throw(ArgumentError("the threshold must be positive"))
                threshold = numbers[1]
            else
                throw(ArgumentError("unknown statement '$key'"))
            end
        catch err
            err isa ArgumentError || rethrow()
            throw(ArgumentError("line $number: $(err.msg)"))
        end
    end
    net.sites > 0 || throw(ArgumentError("the file defines no sites"))
    duration > 0 || throw(ArgumentError("the file has no run statement"))
    for k in kicks
        1 <= k.site <= net.sites || throw(ArgumentError("a kick names site $(k.site), which does not exist"))
        0 <= k.time < duration || throw(ArgumentError("the kick at time $(k.time) lies outside the run"))
    end
    return Case(title, laser, net, kicks, duration, threshold, expectations)
end

load_case(path::AbstractString) = parse_case(read(path, String))

run_case(case::Case; step::Real = 0.02) =
    simulate(case.network, case.laser, case.kicks, case.duration; threshold = case.threshold, step = step)
