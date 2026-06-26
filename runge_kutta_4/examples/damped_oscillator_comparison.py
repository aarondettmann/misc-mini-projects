"""Generate an RK4 vs exact-solution comparison for a damped oscillator."""

from __future__ import annotations

from math import cos, exp, sin, sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from ode.solver import rk4


def rhs(_t: float, y: tuple[float, float]) -> tuple[float, float]:
    """Damped harmonic oscillator: x' = v, v' = -2*gamma*v - omega0^2*x."""
    gamma = 0.15
    omega0 = 1.4
    x, v = y
    return v, -2.0 * gamma * v - (omega0**2) * x


def exact_solution(times: list[float]) -> tuple[list[float], list[float]]:
    """Closed-form solution for x(0)=1, v(0)=0."""
    gamma = 0.15
    omega0 = 1.4
    omega_d = sqrt((omega0**2) - (gamma**2))

    exact_x = []
    exact_v = []
    for t in times:
        decay = exp(-gamma * t)
        cos_term = cos(omega_d * t)
        sin_term = sin(omega_d * t)
        exact_x.append(decay * (cos_term + (gamma / omega_d) * sin_term))
        exact_v.append(-decay * ((omega0**2) / omega_d) * sin_term)
    return exact_x, exact_v


def main() -> Path:
    times, states = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.05, n_steps=400)
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
