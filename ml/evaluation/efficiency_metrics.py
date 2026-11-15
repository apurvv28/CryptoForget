"""
Efficiency Metrics and Break-Even Analysis.

Per Doc 08 (§4): Measures speedup, time saved, step reduction,
and SISA initial cost amortization:
    Speedup = T_full_del / T_sisa_del
    TimeSavedPct = ((T_full_del - T_sisa_del) / T_full_del) * 100
    N_break_even = T_init_sisa / (T_full_del - T_sisa_del)
"""

from typing import Any


def calculate_efficiency_metrics(
    t_init_sisa: float,
    t_full_del: float,
    t_sisa_del: float,
    steps_full: int,
    steps_sisa: int,
) -> dict[str, Any]:
    """
    Computes comparative efficiency metrics between SISA selective unlearning
    and clean full retraining.
    """
    speedup = round(t_full_del / max(1e-5, t_sisa_del), 2)
    time_saved_pct = round(((t_full_del - t_sisa_del) / max(1e-5, t_full_del)) * 100, 2)
    step_reduction_pct = round(((steps_full - steps_sisa) / max(1, steps_full)) * 100, 2)

    time_diff = t_full_del - t_sisa_del
    if time_diff > 0:
        break_even_requests = round(t_init_sisa / time_diff, 1)
    else:
        break_even_requests = float("inf")

    return {
        "t_init_sisa_sec": round(t_init_sisa, 2),
        "t_full_del_sec": round(t_full_del, 2),
        "t_sisa_del_sec": round(t_sisa_del, 2),
        "speedup": speedup,
        "time_saved_pct": time_saved_pct,
        "steps_full": steps_full,
        "steps_sisa": steps_sisa,
        "step_reduction_pct": step_reduction_pct,
        "break_even_requests": break_even_requests,
    }
