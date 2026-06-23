"""Readable NumPy reference implementation of classical RK4."""

from collections.abc import Callable, Sequence
from numbers import Real

import numpy as np

State = float | Sequence[Real]
RHS = Callable[[float, State], State]
Vector = np.ndarray


def _as_scalar(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("rhs must return a real number for scalar y")
    return float(value)


def _as_vector(value: object, expected_dim: int) -> Vector:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("rhs must return a sequence with the same length as y")

    if len(value) != expected_dim:
        raise ValueError("rhs return length must match y dimension")

    if not all(
        isinstance(component, Real) and not isinstance(component, bool)
        for component in value
    ):
        raise TypeError("rhs return sequence must contain only real numbers")

    return np.asarray(value, dtype=np.float64)


def _validate_inputs(
    rhs: RHS,
    t0: float,
    h: float,
    n_steps: int,
) -> tuple[float, float]:
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

    return float(t0), float(h)


def _rk4_scalar(
    rhs: RHS,
    t: float,
    y: float,
    h: float,
    n_steps: int,
) -> tuple[list[float], list[object]]:
    half_h = 0.5 * h
    sixth_h = h / 6.0

    times = [t]
    states: list[object] = [y]

    for _ in range(n_steps):
        k1 = _as_scalar(rhs(t, y))
        k2 = _as_scalar(rhs(t + half_h, y + half_h * k1))
        k3 = _as_scalar(rhs(t + half_h, y + half_h * k2))
        k4 = _as_scalar(rhs(t + h, y + h * k3))

        y += sixth_h * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += h

        times.append(t)
        states.append(y)

    return times, states


def _rk4_vector(
    rhs: RHS,
    t: float,
    y: Vector,
    h: float,
    n_steps: int,
) -> tuple[list[float], list[object]]:
    half_h = 0.5 * h
    sixth_h = h / 6.0
    dim = y.size

    def eval_rhs(t: float, y: Vector) -> Vector:
        return _as_vector(rhs(t, tuple(map(float, y))), dim)

    times = [t]
    states: list[object] = [tuple(map(float, y))]

    for _ in range(n_steps):
        k1 = eval_rhs(t, y)
        k2 = eval_rhs(t + half_h, y + half_h * k1)
        k3 = eval_rhs(t + half_h, y + half_h * k2)
        k4 = eval_rhs(t + h, y + h * k3)

        y += sixth_h * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += h

        times.append(t)
        states.append(tuple(map(float, y)))

    return times, states


def rk4_numpy(
    rhs: RHS,
    t0: float,
    y0: State,
    h: float,
    n_steps: int,
) -> tuple[list[float], list[object]]:
    """Integrate an ODE with fixed-step classical RK4 using NumPy."""
    t, h = _validate_inputs(rhs, t0, h, n_steps)

    if isinstance(y0, Real) and not isinstance(y0, bool):
        return _rk4_scalar(rhs, t, float(y0), h, n_steps)

    if isinstance(y0, (str, bytes)) or not isinstance(y0, Sequence):
        raise TypeError("y0 must be a real number or a sequence of real numbers")

    if len(y0) == 0:
        raise ValueError("y0 sequence must not be empty")

    y = _as_vector(y0, len(y0))
    return _rk4_vector(rhs, t, y, h, n_steps)
