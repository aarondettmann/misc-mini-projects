import pytest

from ode.solver import rk4


def test_rk4_rejects_non_callable_rhs() -> None:
    with pytest.raises(TypeError, match="rhs must be callable"):
        rk4(rhs=42, t0=0.0, y0=1.0, h=0.1, n_steps=10)  # type: ignore[arg-type]


def test_rk4_rejects_zero_step_size() -> None:
    with pytest.raises(ValueError, match="h must be finite and non-zero"):
        rk4(rhs=lambda _t, y: y, t0=0.0, y0=1.0, h=0.0, n_steps=10)


def test_rk4_rejects_invalid_step_count() -> None:
    with pytest.raises(ValueError, match="n_steps must be greater than 0"):
        rk4(rhs=lambda _t, y: y, t0=0.0, y0=1.0, h=0.1, n_steps=0)


def test_rk4_rejects_invalid_state_type() -> None:
    with pytest.raises(
        TypeError, match="y0 must be a real number or a sequence of real numbers"
    ):
        rk4(rhs=lambda _t, y: y, t0=0.0, y0="invalid", h=0.1, n_steps=10)  # type: ignore[arg-type]


def test_rk4_scalar_output_shape() -> None:
    times, states = rk4(rhs=lambda _t, y: y, t0=0.0, y0=1.0, h=0.1, n_steps=5)
    assert len(times) == 6
    assert len(states) == 6
    assert all(isinstance(v, float) for v in states)


def test_rk4_vector_output_shape() -> None:
    def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
        return (y[1], -y[0])

    times, states = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.1, n_steps=5)
    assert len(times) == 6
    assert len(states) == 6
    assert all(len(state) == 2 for state in states)
