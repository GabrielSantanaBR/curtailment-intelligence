"""Linear optimization for curtailment mitigation scenarios."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog


def optimize_dispatch(payload: dict) -> dict:
    available = np.array(payload["curtailed_profile_mwh"], dtype=float)
    if np.any(available < 0):
        raise ValueError("curtailed_profile_mwh cannot contain negative values")

    periods = len(available)
    capacity = float(payload["battery_capacity_mwh"])
    initial_soc = min(float(payload["battery_initial_soc_mwh"]), capacity)
    charge_limit = float(payload["battery_max_charge_mw"])
    roundtrip_efficiency = float(payload["battery_roundtrip_efficiency"])
    charge_efficiency = np.sqrt(roundtrip_efficiency)
    flexible_power_limit = float(payload["flexible_load_capacity_mw"])
    flexible_energy_budget = float(payload["flexible_load_total_mwh"])

    # Variables:
    #   x[0:n]   = battery charge from curtailed energy in each hour
    #   x[n:2n]  = flexible-load consumption in each hour
    # Objective maximizes recoverable energy.
    objective = np.r_[
        -np.ones(periods) * charge_efficiency,
        -np.ones(periods),
    ]

    bounds = [
        (0, min(charge_limit, available[index])) for index in range(periods)
    ] + [
        (0, min(flexible_power_limit, available[index])) for index in range(periods)
    ]

    inequalities: list[np.ndarray] = []
    upper_bounds: list[float] = []

    # Source-energy balance for each hour.
    for index in range(periods):
        row = np.zeros(2 * periods)
        row[index] = 1
        row[periods + index] = 1
        inequalities.append(row)
        upper_bounds.append(available[index])

    # Battery state-of-charge must not exceed its free capacity at any prefix.
    free_capacity = max(0, capacity - initial_soc)
    for index in range(periods):
        row = np.zeros(2 * periods)
        row[: index + 1] = charge_efficiency
        inequalities.append(row)
        upper_bounds.append(free_capacity)

    # Flexible-load total energy budget.
    row = np.zeros(2 * periods)
    row[periods:] = 1
    inequalities.append(row)
    upper_bounds.append(flexible_energy_budget)

    result = linprog(
        objective,
        A_ub=np.array(inequalities),
        b_ub=np.array(upper_bounds),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    battery = result.x[:periods]
    flexible = result.x[periods:]
    state_of_charge = initial_soc
    dispatch: list[dict] = []
    total_recovered = 0.0

    for index in range(periods):
        state_of_charge = min(
            capacity,
            state_of_charge + battery[index] * charge_efficiency,
        )
        recovered = min(
            available[index],
            battery[index] * charge_efficiency + flexible[index],
        )
        lost = max(0, available[index] - recovered)
        total_recovered += recovered

        dispatch.append(
            {
                "hour": index,
                "available_mwh": round(float(available[index]), 3),
                "battery_charge_mwh": round(float(battery[index]), 3),
                "flexible_load_mwh": round(float(flexible[index]), 3),
                "recovered_mwh": round(float(recovered), 3),
                "lost_mwh": round(float(lost), 3),
                "battery_soc_mwh": round(float(state_of_charge), 3),
            }
        )

    total_available = float(available.sum())
    lost = max(0, total_available - total_recovered)
    recovery_rate = 100 * total_recovered / total_available if total_available else 0

    has_battery = capacity > 0 and charge_limit > 0
    has_flexible_load = flexible_energy_budget > 0 and flexible_power_limit > 0
    if has_battery and has_flexible_load:
        strategy = "battery + flexible load"
    elif has_battery:
        strategy = "battery"
    elif has_flexible_load:
        strategy = "flexible load"
    else:
        strategy = "no mitigation resource"

    return {
        "plant_code": payload.get("plant_code", "unknown"),
        "total_available_mwh": round(total_available, 3),
        "recovered_mwh": round(total_recovered, 3),
        "lost_mwh": round(lost, 3),
        "recovery_rate_pct": round(recovery_rate, 2),
        "estimated_value_preserved_brl": round(
            total_recovered * float(payload["energy_value_brl_mwh"]),
            2,
        ),
        "estimated_avoided_tco2": round(
            total_recovered * float(payload["grid_factor_tco2_mwh"]),
            3,
        ),
        "strategy_summary": strategy,
        "dispatch": dispatch,
        "assumptions": [
            "Each interval is one hour.",
            "Battery output is represented as stored recoverable energy inside the study horizon; discharge economics are not modeled.",
            "Flexible load is a scenario resource constrained by hourly and total-energy limits.",
            "Grid feasibility, asset location, connection limits and market rules must be validated with the thematic specialist.",
            "Avoided-emissions and economic values are scenario estimates driven by user-configurable factors.",
        ],
    }
