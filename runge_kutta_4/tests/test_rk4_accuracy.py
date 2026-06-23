import math

import pytest

from ode.solver import rk4


def test_rk4_exponential_growth_accuracy() -> None:
    times, states = rk4(rhs=lambda _t, y: y, t0=0.0, y0=1.0, h=0.1, n_steps=10)
    assert times[-1] == pytest.approx(1.0)
    assert states[-1] == pytest.approx(math.e, rel=1e-4, abs=1e-4)


def test_rk4_harmonic_oscillator_accuracy() -> None:
    def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
        x, v = y
        return (v, -x)

    n_steps = 1000
    h = (2.0 * math.pi) / n_steps
    _, states = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=h, n_steps=n_steps)

    final_x, final_v = states[-1]
    assert final_x == pytest.approx(1.0, rel=1e-3, abs=1e-3)
    assert final_v == pytest.approx(0.0, rel=1e-3, abs=1e-3)
