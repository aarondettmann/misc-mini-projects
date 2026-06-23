"""Python-facing RK4 solver API backed by a C extension core."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from numbers import Real

from . import _rk4

State = float | Sequence[float]
RHS = Callable[[float, State], State]


def _is_numeric_sequence(value: object) -> bool:
    # Accept plain numeric sequences for vector-valued states, but reject text.
    if isinstance(value, (str, bytes)):
        return False
    if not isinstance(value, Sequence):
        return False
    return all(isinstance(component, Real) for component in value)


def rk4(
    rhs: RHS, t0: float, y0: State, h: float, n_steps: int
) -> tuple[list[float], list[object]]:
    """Integrate an ODE with fixed-step classical RK4.

    Args:
        rhs: Callable RHS function f(t, y) -> dy/dt.
        t0: Initial time.
        y0: Initial state as a scalar or a numeric sequence.
        h: Step size (must be non-zero).
        n_steps: Number of fixed integration steps (must be > 0).

    Returns:
        A tuple `(times, states)`.
    """
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

    if isinstance(y0, Real) and not isinstance(y0, bool):
        normalized_y0: State = float(y0)
    elif _is_numeric_sequence(y0):
        if len(y0) == 0:  # type: ignore[arg-type]
            raise ValueError("y0 sequence must not be empty")
        # Normalize to a tuple of floats so the C core sees a predictable shape.
        normalized_y0 = tuple(float(component) for component in y0)  # type: ignore[arg-type]
    else:
        raise TypeError("y0 must be a real number or a sequence of real numbers")

    times, states = _rk4.integrate(
        rhs, float(t0), normalized_y0, float(h), int(n_steps)
    )
    return times, states
