"""
Python-facing RK4 solver API backed by a C extension core.
"""

from collections.abc import Callable, Sequence
import math
from numbers import Real
from typing import overload

from . import _rk4

State = Real | Sequence[Real]
RHS = Callable[[float, State], State]


def _require_real(name: str, value: object) -> float:
    """Validate that *value* is a real number (excluding bool) and return it as a float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    return float(value)


def _normalize_state(y0: State) -> State:
    """Normalize the initial state into the representation expected by the C extension."""
    if isinstance(y0, bool):
        raise TypeError("y0 cannot be bool")

    if isinstance(y0, Real):
        return float(y0)

    if isinstance(y0, (str, bytes)):
        raise TypeError("y0 must be a real number or a sequence of real numbers")

    return tuple(y0)


@overload
def rk4(
    rhs: Callable[[float, float], float],
    t0: float,
    y0: Real,
    h: float,
    n_steps: int,
) -> tuple[list[float], list[float]]: ...


@overload
def rk4(
    rhs: Callable[[float, Sequence[Real]], Sequence[Real]],
    t0: float,
    y0: Sequence[Real],
    h: float,
    n_steps: int,
) -> tuple[list[float], list[tuple[float, ...]]]: ...


def rk4(
    rhs: RHS,
    t0: float,
    y0: State,
    h: float,
    n_steps: int,
) -> tuple[list[float], list[object]]:
    """
    Integrate an ODE using the classical fixed-step fourth-order Runge–Kutta method.

    The numerical integration is performed by the underlying C extension.

    Args:
        rhs: Right-hand side function ``f(t, y)``.
        t0: Initial time.
        y0: Initial state (scalar or sequence).
        h: Step size (finite and non-zero).
        n_steps: Number of integration steps (> 0).

    Returns:
        A pair ``(times, states)``.

    Raises:
        TypeError: If argument types are invalid.
        ValueError: If numeric constraints are violated.
    """
    if not callable(rhs):
        raise TypeError("rhs must be callable")

    t0 = _require_real("t0", t0)
    h = _require_real("h", h)

    if not math.isfinite(h) or h == 0.0:
        raise ValueError("h must be finite and non-zero")

    if isinstance(n_steps, bool) or not isinstance(n_steps, int):
        raise TypeError("n_steps must be an integer")

    if n_steps <= 0:
        raise ValueError("n_steps must be greater than 0")

    y0 = _normalize_state(y0)

    return _rk4.integrate(rhs, t0, y0, h, n_steps)
