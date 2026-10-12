"""Deterministic local mission forecast and reserve-risk calculations."""

from dataclasses import dataclass
from numbers import Integral
from typing import TypedDict


class ReserveViolation(TypedDict):
    hour: int
    reserve: float
    shortfall: float


@dataclass(frozen=True)
class MissionScenario:
    schedule: tuple[str, ...]
    energy_costs: tuple[float, ...]
    solar_recovery: tuple[float, ...]
    objectives: tuple[tuple[int, str], ...]


SCENARIOS: dict[str, MissionScenario] = {
    "Debris Conjunction": MissionScenario(
        schedule=("Coast", "Avoidance burn", "Reorientation", "Coast", "Downlink", "Recovery"),
        energy_costs=(3.0, 4.4, 3.6, 4.8, 3.5, 3.9),
        solar_recovery=(0.2, 0.4, 0.3, 0.3, 0.8, 0.4),
        objectives=(
            (4, "Debris avoidance burn"),
            (8, "Safe vector confirmed"),
            (12, "Downlink complete"),
        ),
    ),
    "Solar Flare Window": MissionScenario(
        schedule=("Safe attitude", "Flare entry", "Radiation hold", "Instrument check", "Flare exit", "Recovery"),
        energy_costs=(3.8, 5.4, 5.8, 4.7, 5.0, 4.2),
        solar_recovery=(0.1, 0.0, 0.0, 0.2, 0.5, 0.8),
        objectives=(
            (2, "Flare-safe attitude reached"),
            (6, "Radiation hold complete"),
            (10, "Flare window clear"),
        ),
    ),
    "Lunar Transfer": MissionScenario(
        schedule=("Injection", "Transfer coast", "Mid-course correction", "Transfer coast", "Lunar capture", "Orbit trim"),
        energy_costs=(5.2, 3.7, 5.5, 3.8, 5.8, 4.9),
        solar_recovery=(0.2, 0.5, 0.1, 0.5, 0.2, 0.3),
        objectives=(
            (2, "Injection confirmed"),
            (8, "Mid-course correction complete"),
            (12, "Lunar capture complete"),
        ),
    ),
    "Deep Space Relay": MissionScenario(
        schedule=("Relay coast", "Array alignment", "Relay window", "Data relay", "Relay coast", "Signal handoff"),
        energy_costs=(4.2, 4.6, 3.8, 4.8, 4.1, 4.5),
        solar_recovery=(1.0, 1.4, 1.2, 0.8, 1.1, 0.7),
        objectives=(
            (4, "Array aligned"),
            (8, "Relay downlink complete"),
            (12, "Signal handoff complete"),
        ),
    ),
}

MODE_ENERGY_FACTOR = {
    "Autonomous": 1.0,
    "Manual": 1.08,
    "Safe Hold": 0.72,
}
INITIAL_BATTERY = 92.0
FORECAST_STEP_HOURS = 2
WATCH_TOLERANCE = 5.0


def validate_inputs(scenario: str, reserve_target: int, mode: str) -> None:
    if not isinstance(scenario, str):
        raise ValueError("Mission scenario must be a string.")
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown mission scenario: {scenario!r}")
    if isinstance(reserve_target, bool) or not isinstance(reserve_target, Integral):
        raise ValueError("Battery reserve target must be an integer.")

    reserve_target = int(reserve_target)
    if not 20 <= reserve_target <= 80:
        raise ValueError("Battery reserve target must be between 20 and 80%.")
    if not isinstance(mode, str):
        raise ValueError("Monitoring mode must be a string.")
    if mode not in MODE_ENERGY_FACTOR:
        raise ValueError(f"Unknown monitoring mode: {mode!r}")


def calculate_mission(scenario: str, reserve_target: int, mode: str) -> dict:
    """Return one physical forecast plus risk classifications for its reserve target.

    SAFE means no forecast point falls below the target. WATCH means the forecast
    falls below it by at most five percentage points. CRITICAL means any point
    falls more than five percentage points below it.
    """
    validate_inputs(scenario, reserve_target, mode)
    reserve_target = int(reserve_target)
    mission = SCENARIOS[scenario]
    mode_factor = MODE_ENERGY_FACTOR[mode]
    effective_energy_costs = [
        round(energy_cost * mode_factor, 2)
        for energy_cost in mission.energy_costs
    ]

    hours = [0]
    battery = [INITIAL_BATTERY]
    for energy_cost, solar_recovery in zip(
        effective_energy_costs, mission.solar_recovery
    ):
        net_draw = energy_cost - solar_recovery
        battery.append(round(max(0.0, min(100.0, battery[-1] - net_draw)), 2))
        hours.append(hours[-1] + FORECAST_STEP_HOURS)

    violations: list[ReserveViolation] = [
        {
            "hour": hour,
            "reserve": reserve,
            "shortfall": round(reserve_target - reserve, 2),
        }
        for hour, reserve in zip(hours[1:], battery[1:])
        if reserve < reserve_target
    ]
    maximum_shortfall = max((item["shortfall"] for item in violations), default=0.0)
    status = (
        "SAFE"
        if not violations
        else "WATCH"
        if maximum_shortfall <= WATCH_TOLERANCE
        else "CRITICAL"
    )
    risk = {"SAFE": "Low", "WATCH": "Moderate", "CRITICAL": "High"}[status]

    objectives = [
        {
            "name": name,
            "hour": hour,
            "reserve": battery[hours.index(hour)],
            "threatened": battery[hours.index(hour)] < reserve_target,
        }
        for hour, name in mission.objectives
    ]
    threatened_objectives = [item for item in objectives if item["threatened"]]
    total_shortfall = sum(item["shortfall"] for item in violations)
    drift_score = round(
        min(100.0, total_shortfall + len(threatened_objectives) * 5.0), 1
    )

    return {
        "scenario": scenario,
        "mode": mode,
        "reserve_target": reserve_target,
        "hours": hours,
        "battery": battery,
        "required_reserve": [float(reserve_target)] * len(hours),
        "schedule": list(mission.schedule),
        "energy_costs": effective_energy_costs,
        "solar_recovery": list(mission.solar_recovery),
        "minimum_reserve": min(battery),
        "minimum_reserve_hour": hours[battery.index(min(battery))],
        "violations": violations,
        "objectives": objectives,
        "threatened_objectives": threatened_objectives,
        "status": status,
        "risk": risk,
        "drift_score": drift_score,
    }
