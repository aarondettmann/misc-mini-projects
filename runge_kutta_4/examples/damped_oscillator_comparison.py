"""
Generate an RK4 vs exact-solution comparison for a damped oscillator.

See also:

https://en.wikipedia.org/wiki/Harmonic_oscillator#Damped_harmonic_oscillator

---

The second-order ODE reads

    m*x'' + c*x' + k*x = 0

Divide by m and define standard parameters:

    omega0**2  = k/m        (natural frequency squared)
    gamma      = c/(2*m)    (damping coefficient)

This gives the form:

    x'' + 2*gamma*x' + omega0**2*x = 0


Convert to a first-order system for RK4:

Let:
    x = position
    v = x' = velocity

Then:

    dx/dt = v

    dv/dt = -2*gamma*v - omega0**2*x


State vector:
    y = [x, v]

Derivative function:
    f(t, y) = [
        v,
        -2*gamma*v - omega0**2*x
    ]
"""

from math import cos, exp, sin, sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from ode.solver import rk4

GAMMA = 0.15
OMEGA0 = 1.4


def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
    """Damped harmonic oscillator: x' = v, v' = -2*GAMMA*v - OMEGA0^2*x."""
    x, v = y
    return v, -2.0 * GAMMA * v - (OMEGA0**2) * x


def exact_solution(times: list[float]) -> tuple[list[float], list[float]]:
    """Closed-form solution for x(0)=1, v(0)=0."""
    omega_d = sqrt((OMEGA0**2) - (GAMMA**2))

    exact_x = []
    exact_v = []
    for t in times:
        decay = exp(-GAMMA * t)
        cos_term = cos(omega_d * t)
        sin_term = sin(omega_d * t)
        exact_x.append(decay * (cos_term + (GAMMA / omega_d) * sin_term))
        exact_v.append(-decay * ((OMEGA0**2) / omega_d) * sin_term)

    return exact_x, exact_v


def main() -> Path:
    times, states = rk4(
        rhs=rhs,
        t0=0.0,
        y0=(1.0, 0.0),
        h=0.05,
        n_steps=400,
    )
    rk4_x = [state[0] for state in states]
    rk4_v = [state[1] for state in states]
    exact_x, exact_v = exact_solution(times)

    fig, (ax_time, ax_phase) = plt.subplots(1, 2, figsize=(11, 4))

    ax_time.plot(times, exact_x, "-", label="Exact")
    ax_time.plot(times, rk4_x, "--", label="RK4")
    ax_time.set_title("Displacement over time")
    ax_time.set_xlabel("t")
    ax_time.set_ylabel("x(t)")
    ax_time.grid(True)
    ax_time.legend()

    ax_phase.plot(exact_x, exact_v, "-", label="Exact")
    ax_phase.plot(rk4_x, rk4_v, "--", label="RK4")
    ax_phase.set_title("Phase portrait")
    ax_phase.set_xlabel("x")
    ax_phase.set_ylabel("v")
    ax_phase.grid(True)
    ax_phase.legend()

    fig.suptitle("Damped harmonic oscillator: RK4 vs exact solution")
    fig.tight_layout()

    output_path = Path(__file__).with_name("rk4_vs_exact_damped_oscillator.png")
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return output_path


if __name__ == "__main__":
    print(main())
