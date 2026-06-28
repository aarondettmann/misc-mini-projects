import math

import pytest

from ode.solver import velocity_verlet


def test_velocity_verlet_harmonic_oscillator_accuracy() -> None:
    def acceleration(_t: float, q: tuple[float]) -> tuple[float]:
        return (-q[0],)

    n_steps = 4000
    h = (2.0 * math.pi) / n_steps
    _, states = velocity_verlet(
        acceleration=acceleration,
        t0=0.0,
        q0=(1.0,),
        v0=(0.0,),
        h=h,
        n_steps=n_steps,
    )

    final_q, final_v = states[-1]
    assert final_q == pytest.approx(1.0, rel=1e-3, abs=1e-3)
    assert final_v == pytest.approx(0.0, rel=1e-3, abs=1e-3)
