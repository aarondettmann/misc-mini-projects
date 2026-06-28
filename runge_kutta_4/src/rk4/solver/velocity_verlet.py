"""Velocity-Verlet symplectic integrator API."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from numbers import Real

State = tuple[float, ...]
Acceleration = Callable[[float, State], Sequence[float]]


def _normalize_real_sequence(value: object, name: str) -> State:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of real numbers")
    if len(value) == 0:
        raise ValueError(f"{name} sequence must not be empty")

    normalized: list[float] = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, Real):
            raise TypeError(f"{name} must be a sequence of real numbers")
        normalized.append(float(component))
    return tuple(normalized)


def velocity_verlet(
    acceleration: Acceleration,
    t0: float,
    q0: Sequence[float],
    v0: Sequence[float],
    h: float,
    n_steps: int,
) -> tuple[list[float], list[State]]:
    """Integrate a second-order system with the velocity-Verlet method."""
    if not callable(acceleration):
        raise TypeError("acceleration must be callable")
    if isinstance(t0, bool) or not isinstance(t0, Real):
        raise TypeError("t0 must be a real number")
    if isinstance(h, bool) or not isinstance(h, Real):
        raise TypeError("h must be a real number")
    if float(h) == 0.0:
        raise ValueError("h must be non-zero")
    if isinstance(n_steps, bool) or not isinstance(n_steps, int):
        raise TypeError("n_steps must be an integer")
    if n_steps <= 0:
        raise ValueError("n_steps must be greater than 0")

    q = _normalize_real_sequence(q0, "q0")
    v = _normalize_real_sequence(v0, "v0")
    if len(q) != len(v):
        raise ValueError("q0 and v0 must have the same length")

    dimension = len(q)
    t = float(t0)
    step_size = float(h)
    times = [t]
    states: list[State] = [q + v]

    acceleration_values = _normalize_real_sequence(acceleration(t, q), "acceleration return")
    if len(acceleration_values) != dimension:
        raise ValueError("acceleration return length must match q dimension")

    current_acceleration = acceleration_values
    current_q = q
    current_v = v

    for _ in range(n_steps):
        v_half = tuple(
            current_v[index] + 0.5 * step_size * current_acceleration[index]
            for index in range(dimension)
        )
        next_q = tuple(
            current_q[index] + step_size * v_half[index] for index in range(dimension)
        )

        next_t = t + step_size
        next_acceleration = _normalize_real_sequence(
            acceleration(next_t, next_q), "acceleration return"
        )
        if len(next_acceleration) != dimension:
            raise ValueError("acceleration return length must match q dimension")

        next_v = tuple(
            v_half[index] + 0.5 * step_size * next_acceleration[index]
            for index in range(dimension)
        )

        t = next_t
        current_q = next_q
        current_v = next_v
        current_acceleration = next_acceleration
        times.append(t)
        states.append(current_q + current_v)

    return times, states
