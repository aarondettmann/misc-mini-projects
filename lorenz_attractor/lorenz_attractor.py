"""Simulate the Lorenz attractor with RK4 and render an animation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from ode.solver import rk4


SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
INITIAL_STATE = (1.0, 1.0, 1.0)
STEP = 0.01
N_STEPS = 6000
N_FRAMES = 120
FRAME_DURATION_MS = 200


def lorenz_rhs(_t: float, state: tuple[float, float, float]) -> tuple[float, float, float]:
    """Return the Lorenz vector field at the given state."""
    x, y, z = state
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    return dx, dy, dz


def simulate() -> tuple[np.ndarray, np.ndarray]:
    """Integrate the Lorenz system with the shared RK4 solver."""
    times, states = rk4(rhs=lorenz_rhs, t0=0.0, y0=INITIAL_STATE, h=STEP, n_steps=N_STEPS)
    return np.asarray(times, dtype=float), np.asarray(states, dtype=float)


def build_animation(times: np.ndarray, states: np.ndarray) -> Path:
    """Render the attractor animation and save it as a GIF."""
    x = states[:, 0]
    y = states[:, 1]
    z = states[:, 2]

    frame_indices = np.linspace(1, len(times) - 1, N_FRAMES, dtype=int)

    fig = plt.figure(figsize=(13.5, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0])
    ax_traj = fig.add_subplot(grid[0, 0], projection="3d")
    ax_time = fig.add_subplot(grid[0, 1])

    ax_traj.set_title("Lorenz attractor")
    ax_traj.set_xlabel("x")
    ax_traj.set_ylabel("y")
    ax_traj.set_zlabel("z")
    ax_traj.set_xlim(float(x.min()), float(x.max()))
    ax_traj.set_ylim(float(y.min()), float(y.max()))
    ax_traj.set_zlim(float(z.min()), float(z.max()))
    ax_traj.set_box_aspect((1.0, 1.0, 0.75))

    ax_time.set_title("State variables over time")
    ax_time.set_xlabel("t")
    ax_time.set_ylabel("value")
    ax_time.grid(True, alpha=0.3)
    ax_time.set_xlim(float(times[0]), float(times[-1]))
    y_min = float(np.min(states))
    y_max = float(np.max(states))
    ax_time.set_ylim(y_min, y_max)

    (traj_line,) = ax_traj.plot([], [], [], color="#1f77b4", lw=1.1, alpha=0.95)
    (traj_head,) = ax_traj.plot([], [], [], marker="o", ms=5, color="#ff7f0e")
    (x_line,) = ax_time.plot([], [], color="#2ca02c", lw=1.3, label="x(t)")
    (y_line,) = ax_time.plot([], [], color="#7b2cbf", lw=1.2, label="y(t)")
    (z_line,) = ax_time.plot([], [], color="#d62728", lw=1.2, label="z(t)")
    (x_head,) = ax_time.plot([], [], marker="o", ms=4, color="#2ca02c")
    (y_head,) = ax_time.plot([], [], marker="o", ms=4, color="#7b2cbf")
    (z_head,) = ax_time.plot([], [], marker="o", ms=4, color="#d62728")
    time_marker = ax_time.axvline(0.0, color="#ff7f0e", lw=1.0, alpha=0.7)
    info_text = ax_traj.text2D(0.03, 0.96, "", transform=ax_traj.transAxes)
    ax_time.legend(loc="upper right", frameon=False)

    def update(frame_number: int):
        index = int(frame_indices[frame_number])
        current_times = times[: index + 1]
        current_x = x[: index + 1]
        current_y = y[: index + 1]
        current_z = z[: index + 1]

        traj_line.set_data(current_x, current_y)
        traj_line.set_3d_properties(current_z)
        traj_head.set_data([x[index]], [y[index]])
        traj_head.set_3d_properties([z[index]])

        x_line.set_data(current_times, current_x)
        y_line.set_data(current_times, current_y)
        z_line.set_data(current_times, current_z)
        x_head.set_data([times[index]], [x[index]])
        y_head.set_data([times[index]], [y[index]])
        z_head.set_data([times[index]], [z[index]])
        time_marker.set_xdata([times[index], times[index]])
        info_text.set_text(
            f"t = {times[index]:5.2f}\n"
            f"(x, y, z) = ({x[index]:.2f}, {y[index]:.2f}, {z[index]:.2f})"
        )
        ax_traj.view_init(elev=28.0, azim=45.0 + 0.35 * frame_number)
        return (
            traj_line,
            traj_head,
            x_line,
            y_line,
            z_line,
            x_head,
            y_head,
            z_head,
            time_marker,
            info_text,
        )

    output_path = Path(__file__).with_name("lorenz_attractor.gif")
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


def save_snapshot(times: np.ndarray, states: np.ndarray) -> Path:
    """Save a static summary plot for the README."""
    x = states[:, 0]
    y = states[:, 1]
    z = states[:, 2]

    fig = plt.figure(figsize=(11, 7), constrained_layout=True)
    ax_traj = fig.add_subplot(1, 2, 1, projection="3d")
    ax_time = fig.add_subplot(1, 2, 2)

    ax_traj.plot(x, y, z, color="#1f77b4", lw=0.8)
    ax_traj.set_title("Lorenz attractor")
    ax_traj.set_xlabel("x")
    ax_traj.set_ylabel("y")
    ax_traj.set_zlabel("z")
    ax_traj.set_box_aspect((1.0, 1.0, 0.75))
    ax_traj.view_init(elev=24.0, azim=42.0)

    ax_time.plot(times, x, color="#2ca02c", lw=1.1)
    ax_time.set_title("x(t)")
    ax_time.set_xlabel("t")
    ax_time.set_ylabel("x")
    ax_time.grid(True, alpha=0.3)

    fig.suptitle("Lorenz attractor simulated with RK4")
    output_path = Path(__file__).with_name("lorenz_attractor.png")
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    times, states = simulate()
    save_snapshot(times, states)
    animation_path = build_animation(times, states)
    print(animation_path)


if __name__ == "__main__":
    main()
