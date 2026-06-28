import pytest

from ode.solver import velocity_verlet


def test_velocity_verlet_rejects_non_callable_acceleration() -> None:
    with pytest.raises(TypeError, match="acceleration must be callable"):
        velocity_verlet(  # type: ignore[arg-type]
            acceleration=42,
            t0=0.0,
            q0=(1.0,),
            v0=(0.0,),
            h=0.1,
            n_steps=10,
        )


def test_velocity_verlet_rejects_mismatched_state_lengths() -> None:
    with pytest.raises(ValueError, match="q0 and v0 must have the same length"):
        velocity_verlet(
            acceleration=lambda _t, q: q,
            t0=0.0,
            q0=(1.0, 2.0),
            v0=(0.0,),
            h=0.1,
            n_steps=10,
        )


def test_velocity_verlet_vector_output_shape() -> None:
    def acceleration(_t: float, q: tuple[float, float]) -> tuple[float, float]:
        return (-q[0], -q[1])

    times, states = velocity_verlet(
        acceleration=acceleration,
        t0=0.0,
        q0=(1.0, 0.0),
        v0=(0.0, 1.0),
        h=0.1,
        n_steps=5,
    )

    assert len(times) == 6
    assert len(states) == 6
    assert all(len(state) == 4 for state in states)
