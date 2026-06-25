import math

import pytest

from ode.solver import rk4, rk4_numpy


def test_rk4_numpy_rejects_non_callable_rhs() -> None:
    with pytest.raises(TypeError, match="rhs must be callable"):
        rk4_numpy(rhs=42, t0=0.0, y0=1.0, h=0.1, n_steps=5)  # type: ignore[arg-type]


def test_rk4_numpy_rejects_empty_state_sequence() -> None:
    with pytest.raises(ValueError, match="y0 sequence must not be empty"):
        rk4_numpy(rhs=lambda _t, y: y, t0=0.0, y0=(), h=0.1, n_steps=5)


def test_rk4_numpy_scalar_accuracy() -> None:
    times, states = rk4_numpy(rhs=lambda _t, y: y, t0=0.0, y0=1.0, h=0.1, n_steps=10)
    assert times[-1] == pytest.approx(1.0)
    assert states[-1] == pytest.approx(math.e, rel=1e-4, abs=1e-4)


def test_rk4_numpy_vector_output_shape() -> None:
    def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
        x, v = y
        return (v, -x)

    times, states = rk4_numpy(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.1, n_steps=5)
    assert len(times) == 6
    assert len(states) == 6
    assert all(isinstance(state, tuple) for state in states)
    assert all(len(state) == 2 for state in states)


def test_rk4_numpy_matches_c_solver_on_vector_problem() -> None:
    def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
        x, v = y
        return (v, -0.3 * v - x)

    t_numpy, s_numpy = rk4_numpy(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.02, n_steps=600)
    t_c, s_c = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.02, n_steps=600)

    assert t_numpy == pytest.approx(t_c, rel=0.0, abs=1e-12)
    for y_numpy, y_c in zip(s_numpy, s_c, strict=True):
        assert y_numpy == pytest.approx(y_c, rel=1e-11, abs=1e-11)
