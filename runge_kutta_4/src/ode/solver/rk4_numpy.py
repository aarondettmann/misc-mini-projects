"""Readable NumPy reference implementation of classical RK4."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from numbers import Real

import numpy as np

State = float | Sequence[float]
RHS = Callable[[float, State], State]
Vector = np.ndarray


def _is_numeric_sequence(value: object) -> bool:
    if isinstance(value, (str, bytes)):
        return False
    if not isinstance(value, Sequence):
        return False
    return all(isinstance(component, Real) for component in value)


def _as_scalar(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("rhs must return a real number for scalar y")
    return float(value)


def _as_vector(value: object, expected_dim: int) -> np.ndarray:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("rhs must return a sequence with the same length as y")
    if len(value) != expected_dim:  # type: ignore[arg-type]
        raise ValueError("rhs return length must match y dimension")
    if not all(isinstance(component, Real) and not isinstance(component, bool) for component in value):  # type: ignore[arg-type]
        raise TypeError("rhs return sequence must contain only real numbers")
    return np.asarray(value, dtype=np.float64)


def _as_state_tuple(y: Vector) -> tuple[float, ...]:
    return tuple(float(component) for component in y)


def _eval_rhs_vector(rhs: RHS, t: float, y: Vector, expected_dim: int) -> Vector:
    return _as_vector(rhs(t, _as_state_tuple(y)), expected_dim)


def rk4_numpy(
    rhs: RHS, t0: float, y0: State, h: float, n_steps: int
) -> tuple[list[float], list[object]]:
    """Integrate an ODE with fixed-step classical RK4 using NumPy."""
    if not callable(rhs):
        raise TypeError("rhs must be callable")
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

    t = float(t0)
    h_float = float(h)
    times: list[float] = [t]
    states: list[object] = []

    if isinstance(y0, Real) and not isinstance(y0, bool):
        y_scalar = float(y0)
        states.append(y_scalar)
        for _ in range(n_steps):
            k1 = _as_scalar(rhs(t, y_scalar))
            k2 = _as_scalar(rhs(t + 0.5 * h_float, y_scalar + 0.5 * h_float * k1))
            k3 = _as_scalar(rhs(t + 0.5 * h_float, y_scalar + 0.5 * h_float * k2))
            k4 = _as_scalar(rhs(t + h_float, y_scalar + h_float * k3))

            y_scalar += (h_float / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            t += h_float
            times.append(t)
            states.append(y_scalar)
        return times, states

    if not _is_numeric_sequence(y0):
        raise TypeError("y0 must be a real number or a sequence of real numbers")
    if len(y0) == 0:  # type: ignore[arg-type]
        raise ValueError("y0 sequence must not be empty")

    y_vector = np.asarray(y0, dtype=np.float64)
    dim = y_vector.size
    states.append(_as_state_tuple(y_vector))

    for _ in range(n_steps):
        k1 = _eval_rhs_vector(rhs, t, y_vector, dim)
        k2 = _eval_rhs_vector(rhs, t + 0.5 * h_float, y_vector + 0.5 * h_float * k1, dim)
        k3 = _eval_rhs_vector(rhs, t + 0.5 * h_float, y_vector + 0.5 * h_float * k2, dim)
        k4 = _eval_rhs_vector(rhs, t + h_float, y_vector + h_float * k3, dim)

        y_vector = y_vector + (h_float / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += h_float
        times.append(t)
        states.append(_as_state_tuple(y_vector))

    return times, states
