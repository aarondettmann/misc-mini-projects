"""Double pendulum simulation and animation using RK4."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from ode.solver import rk4

# Physical parameters.
G = 9.81
M1 = 1.0
M2 = 1.0
L1 = 1.0
L2 = 1.0

# Numerical parameters.
STEP = 0.005
N_STEPS = 3000
N_FRAMES = 450
FRAME_DURATION_MS = 33
INITIAL_STATE = (2.45, 0.0, 2.15, 0.0)  # (theta1, omega1, theta2, omega2)


def rhs(_t: float, state: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Return state derivative for the planar double pendulum."""
    theta1, omega1, theta2, omega2 = state
    delta = theta1 - theta2

    den = (2.0 * M1 + M2 - M2 * math.cos(2.0 * delta))
    if abs(den) < 1e-9:
        den = 1e-9 if den >= 0.0 else -1e-9

    dtheta1 = omega1
    dtheta2 = omega2

    domega1_num = (
        -G * (2.0 * M1 + M2) * math.sin(theta1)
        - M2 * G * math.sin(theta1 - 2.0 * theta2)
        - 2.0
        * math.sin(delta)
        * M2
        * (omega2**2 * L2 + omega1**2 * L1 * math.cos(delta))
    )
    domega1 = domega1_num / (L1 * den)

    domega2_num = (
        2.0
        * math.sin(delta)
        * (
            omega1**2 * L1 * (M1 + M2)
            + G * (M1 + M2) * math.cos(theta1)
            + omega2**2 * L2 * M2 * math.cos(delta)
        )
    )
    domega2 = domega2_num / (L2 * den)

    return dtheta1, domega1, dtheta2, domega2


def simulate() -> tuple[np.ndarray, np.ndarray]:
    """Integrate the double pendulum dynamics with RK4."""
    times, states = rk4(rhs=rhs, t0=0.0, y0=INITIAL_STATE, h=STEP, n_steps=N_STEPS)
    return np.asarray(times, dtype=float), np.asarray(states, dtype=float)


def to_cartesian(states: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta1 = states[:, 0]
    theta2 = states[:, 2]
    x1 = L1 * np.sin(theta1)
    y1 = -L1 * np.cos(theta1)
    x2 = x1 + L2 * np.sin(theta2)
    y2 = y1 - L2 * np.cos(theta2)
    return x1, y1, x2, y2


def save_snapshot(times: np.ndarray, states: np.ndarray, x2: np.ndarray, y2: np.ndarray) -> Path:
    """Save a static summary figure."""
    fig = plt.figure(figsize=(11.5, 6.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0])
    ax_trace = fig.add_subplot(gs[0, 0])
    ax_phase = fig.add_subplot(gs[0, 1])

    ax_trace.plot(x2, y2, color="#4cc9f0", lw=0.9, alpha=0.95)
    ax_trace.set_title("Tip trajectory")
    ax_trace.set_xlabel("x")
    ax_trace.set_ylabel("y")
    ax_trace.set_aspect("equal", adjustable="box")
    ax_trace.grid(True, alpha=0.3)

    theta1 = states[:, 0]
    omega1 = states[:, 1]
    ax_phase.plot(theta1, omega1, color="#f72585", lw=0.9, alpha=0.95)
    ax_phase.set_title("Phase portrait (theta1, omega1)")
    ax_phase.set_xlabel("theta1")
    ax_phase.set_ylabel("omega1")
    ax_phase.grid(True, alpha=0.3)

    fig.suptitle("Double pendulum chaos (RK4)")
    output_path = Path(__file__).with_name("double_pendulum.png")
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def save_animation(
    times: np.ndarray,
    states: np.ndarray,
    x1: np.ndarray,
    y1: np.ndarray,
    x2: np.ndarray,
    y2: np.ndarray,
) -> Path:
    """Save a GIF animation with pendulum motion and a phase-space panel."""
    frame_indices = np.linspace(1, len(times) - 1, N_FRAMES, dtype=float)
    frame_indices = np.unique(np.rint(frame_indices).astype(int))

    fig = plt.figure(figsize=(12.0, 6.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0])
    ax_pend = fig.add_subplot(gs[0, 0])
    ax_phase = fig.add_subplot(gs[0, 1])

    span = L1 + L2 + 0.25
    ax_pend.set_xlim(-span, span)
    ax_pend.set_ylim(-span, span)
    ax_pend.set_aspect("equal", adjustable="box")
    ax_pend.set_title("Double pendulum")
    ax_pend.set_xlabel("x")
    ax_pend.set_ylabel("y")
    ax_pend.grid(True, alpha=0.25)

    ax_phase.set_title("Phase portrait (theta1, omega1)")
    ax_phase.set_xlabel("theta1")
    ax_phase.set_ylabel("omega1")
    ax_phase.grid(True, alpha=0.3)
    ax_phase.set_xlim(float(states[:, 0].min()), float(states[:, 0].max()))
    ax_phase.set_ylim(float(states[:, 1].min()), float(states[:, 1].max()))

    (rod_line,) = ax_pend.plot([], [], color="#e9ecef", lw=2.2)
    (mass1_dot,) = ax_pend.plot([], [], marker="o", ms=8, color="#f77f00")
    (mass2_dot,) = ax_pend.plot([], [], marker="o", ms=9, color="#d00000")
    (tip_trail,) = ax_pend.plot([], [], color="#4cc9f0", lw=1.1, alpha=0.8)

    (phase_line,) = ax_phase.plot([], [], color="#f72585", lw=1.2, alpha=0.95)
    (phase_head,) = ax_phase.plot([], [], marker="o", ms=5, color="#f72585")

    info_text = ax_pend.text(0.03, 0.95, "", transform=ax_pend.transAxes)

    def update(frame_number: int) -> None:
        i = int(frame_indices[frame_number])
        rod_line.set_data([0.0, x1[i], x2[i]], [0.0, y1[i], y2[i]])
        mass1_dot.set_data([x1[i]], [y1[i]])
        mass2_dot.set_data([x2[i]], [y2[i]])
        tip_trail.set_data(x2[: i + 1], y2[: i + 1])

        theta1_path = states[: i + 1, 0]
        omega1_path = states[: i + 1, 1]
        phase_line.set_data(theta1_path, omega1_path)
        phase_head.set_data([states[i, 0]], [states[i, 1]])

        info_text.set_text(
            f"t = {times[i]:5.2f}\n"
            f"theta1 = {states[i, 0]:+.2f}\n"
            f"theta2 = {states[i, 2]:+.2f}"
        )

    output_path = Path(__file__).with_name("double_pendulum.gif")
    frames: list[Image.Image] = []

    for frame_number in range(len(frame_indices)):
        update(frame_number)
        fig.canvas.draw()
        image = np.asarray(fig.canvas.buffer_rgba())
        frames.append(Image.fromarray(image).convert("P", palette=Image.ADAPTIVE, colors=256))

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=False,
    )
    plt.close(fig)
    return output_path


def main() -> None:
    times, states = simulate()
    x1, y1, x2, y2 = to_cartesian(states)
    save_snapshot(times, states, x2, y2)
    animation_path = save_animation(times, states, x1, y1, x2, y2)
    print(animation_path)


if __name__ == "__main__":
    main()
