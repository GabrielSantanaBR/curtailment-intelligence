import numpy as np
from scipy.optimize import linprog


def optimize_dispatch(payload: dict) -> dict:
    available=np.array(payload["curtailed_profile_mwh"],dtype=float)
    n=len(available)
    cap=float(payload["battery_capacity_mwh"])
    initial=min(float(payload["battery_initial_soc_mwh"]),cap)
    charge_limit=float(payload["battery_max_charge_mw"])
    rte=float(payload["battery_roundtrip_efficiency"])
    charge_eff=np.sqrt(rte)
    flex_limit=float(payload["flexible_load_capacity_mw"])
    flex_total=float(payload["flexible_load_total_mwh"])

    # Variables: battery_charge[n], flexible_load[n]. Objective maximizes immediate recovered MWh.
    # Battery SOC only grows during the curtailment window; later discharge value is represented as stored energy.
    c=np.r_[-np.ones(n)*charge_eff,-np.ones(n)]
    bounds=[(0,min(charge_limit,available[i])) for i in range(n)] + [(0,min(flex_limit,available[i])) for i in range(n)]
    A=[]; b=[]
    # Per-hour recovered source energy cannot exceed curtailed energy.
    for i in range(n):
        row=np.zeros(2*n); row[i]=1; row[n+i]=1
        A.append(row); b.append(available[i])
    # Battery energy state constraint for every prefix.
    for t in range(n):
        row=np.zeros(2*n); row[:t+1]=charge_eff
        A.append(row); b.append(max(0,cap-initial))
    # Flexible-load energy budget.
    row=np.zeros(2*n); row[n:]=1
    A.append(row); b.append(flex_total)
    result=linprog(c,A_ub=np.array(A),b_ub=np.array(b),bounds=bounds,method="highs")
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")
    battery=result.x[:n]; flexible=result.x[n:]
    soc=initial; dispatch=[]
    total_recovered=0.0
    for i in range(n):
        soc=min(cap,soc+battery[i]*charge_eff)
        recovered=min(available[i],battery[i]*charge_eff+flexible[i])
        lost=max(0,available[i]-recovered)
        total_recovered+=recovered
        dispatch.append({
            "hour":i,"available_mwh":round(float(available[i]),3),
            "battery_charge_mwh":round(float(battery[i]),3),
            "flexible_load_mwh":round(float(flexible[i]),3),
            "recovered_mwh":round(float(recovered),3),"lost_mwh":round(float(lost),3),
            "battery_soc_mwh":round(float(soc),3)
        })
    total=float(available.sum()); lost=max(0,total-total_recovered)
    pct=100*total_recovered/total if total else 0
    return {
        "plant_code":payload.get("plant_code","unknown"),
        "total_available_mwh":round(total,3),"recovered_mwh":round(total_recovered,3),
        "lost_mwh":round(lost,3),"recovery_rate_pct":round(pct,2),
        "estimated_value_preserved_brl":round(total_recovered*float(payload["energy_value_brl_mwh"]),2),
        "estimated_avoided_tco2":round(total_recovered*float(payload["grid_factor_tco2_mwh"]),3),
        "strategy_summary":"battery + flexible load" if cap>0 and flex_total>0 else "constrained dispatch",
        "dispatch":dispatch,
        "assumptions":[
            "Each interval is one hour.",
            "Battery output is represented as stored recoverable energy inside the study horizon; discharge economics are not modeled.",
            "Flexible load is a scenario resource constrained by hourly and total-energy limits.",
            "Grid feasibility, asset location, connection limits and market rules must be validated with the thematic specialist.",
            "Avoided-emissions and economic values are scenario estimates driven by user-configurable factors."
        ]
    }
