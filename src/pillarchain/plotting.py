"""Static figures for the report (matplotlib, PNG for the README)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Validated categorical order (fixed, never cycled) + recessive ink.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
NEUTRAL = "#8a8985"
CRITICAL = "#c4271a"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "text.color": INK,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "legend.frameon": False,
        "lines.linewidth": 1.6,
        "figure.dpi": 150,
        "axes.axisbelow": True,
    }
)


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _window(case, result) -> float:
    last = max([k.time for k in case.kicks] + ([result.last_spike] if result.last_spike else []), default=0.0)
    return float(min(case.duration, last + 60.0))


def _raster(ax, result, end: float, start: float = 0.0):
    """Intensity of every site against time, one row per site, on a single-hue scale (square root of intensity)."""
    from matplotlib.colors import PowerNorm

    times = np.linspace(start, end, 900)
    image = result.intensity(times)
    mesh = ax.imshow(
        image,
        aspect="auto",
        origin="lower",
        cmap="Blues",
        norm=PowerNorm(0.5, vmin=0.0, vmax=max(float(image.max()), 1.0)),
        extent=(start, end, 0.5, result.sites + 0.5),
        interpolation="nearest",
    )
    ax.grid(False)
    ax.set_xlabel("time (photon lifetimes)")
    ax.set_ylabel("site")
    return mesh


def case_figure(record: dict, case, result, path) -> None:
    """One figure per case: traces for a few dark or single sites, a raster of site against time otherwise."""
    end = _window(case, result)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    if result.sites <= 8 and result.total == 0 or result.sites == 1:
        times = np.linspace(0.0, end, 1200)
        image = result.intensity(times)
        for site in range(result.sites):
            ax.plot(times, image[site], color=SERIES[site], label=f"site {site + 1}")
        if result.total == 0:
            ax.set_yscale("log")
            ax.set_ylim(bottom=max(float(image.max()) * 1e-6, 1e-14))
        if result.sites > 1:
            ax.legend(ncol=4, fontsize=7)
        ax.set_xlabel("time (photon lifetimes)")
        ax.set_ylabel("intensity")
    else:
        mesh = _raster(ax, result, end)
        fig.colorbar(mesh, ax=ax, label="intensity", pad=0.02)
    ax.set_title(f"{record['case']}: {record['total']} spike(s)", loc="left")
    _save(fig, path)


def overview(speed, critical: float, pumps, shown: dict, path) -> None:
    """Speed against coupling, critical coupling against pump, and two rasters from the library."""
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.6))
    ax = axes[0, 0]
    ok = speed.dropna()
    ax.plot(ok["coupling"], ok["delay per site"], color=SERIES[0], marker="o", ms=4)
    ax.axvline(critical, color=NEUTRAL, lw=1.0, ls="--")
    ax.annotate(
        "critical coupling",
        (critical, ok["delay per site"].max()),
        xytext=(4, -4),
        textcoords="offset points",
        color=INK2,
        fontsize=8,
        va="top",
    )
    ax.set_yscale("log")
    ax.set_xlabel("coupling (per photon lifetime)")
    ax.set_ylabel("delay per site (photon lifetimes)")
    ax.set_title("Pulse speed in a chain", loc="left")
    ax = axes[0, 1]
    ax.plot(pumps["distance below threshold"], pumps["critical coupling"], color=SERIES[0], marker="o", ms=4)
    ax.set_xlabel("distance of the pump below threshold")
    ax.set_ylabel("critical coupling")
    ax.set_ylim(bottom=0)
    ax.set_title("Coupling needed to carry a pulse", loc="left")
    for ax, (title, (case, result)) in zip(axes[1], shown.items(), strict=False):
        _raster(ax, result, min(_window(case, result), 900.0))
        ax.set_title(title, loc="left")
    for ax in axes[1][len(shown) :]:
        ax.set_axis_off()
    _save(fig, path)
