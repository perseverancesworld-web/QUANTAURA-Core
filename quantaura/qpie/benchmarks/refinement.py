"""Grid-refinement studies for discrete topological charges."""

from __future__ import annotations

from typing import Any

from quantaura.qpie.topology import baby_skyrmion_2d, skyrmion_density_2d


def skyrmion_q_vs_resolution(
    sizes: list[int] | None = None,
    radius_frac: float = 0.2,
) -> dict[str, Any]:
    """Compute |Q| for baby skyrmion on successively finer grids."""
    sizes = sizes or [16, 24, 32, 48, 64]
    rows: list[dict[str, Any]] = []
    for n in sizes:
        r0 = max(2.0, radius_frac * n)
        field = baby_skyrmion_2d(n, radius=r0)
        _, q = skyrmion_density_2d(field)
        rows.append(
            {
                "n": n,
                "radius": r0,
                "Q": q,
                "abs_Q": abs(q),
                "err_vs_1": abs(abs(q) - 1.0),
            }
        )
    finest_err = rows[-1]["err_vs_1"]
    coarsest_err = rows[0]["err_vs_1"]
    passed = finest_err < 0.25 and finest_err <= coarsest_err + 0.05
    return {
        "name": "skyrmion_q_refinement",
        "rows": rows,
        "finest_err": finest_err,
        "coarsest_err": coarsest_err,
        "passed": passed,
    }
