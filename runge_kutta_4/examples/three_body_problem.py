"""Simulate a configurable planar three-body problem with a symplectic integrator."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from ode.solver import velocity_verlet

G = 1.0
SOFTENING = 0.0

MASSES = np.array(
    [
        1.1,
        1.2,
        1.3,
    ],
    dtype=float,
)
INITIAL_POSITIONS = np.array(
    [
        (-1, 0.25),
        (1, -0.24),
        (0.0, 0.0),
    ],
    dtype=float,
)
INITIAL_VELOCITIES = np.array(
    [
        (0.47, 0.42),
        (0.48, 0.41),
        (-0.90, -0.90),
    ],
    dtype=float,
)

STEP = 0.003
N_STEPS = 5000
N_FRAMES = 360
FRAME_DURATION_MS = 33


def _flatten_positions(positions: np.ndarray) -> tuple[float, ...]:
    return tuple(float(component) for component in positions.reshape(-1))


def acceleration(_t: float, positions_flat: tuple[float, ...]) -> tuple[float, ...]:
    """Return gravitational accelerations for the planar three-body system."""
    positions = np.asarray(positions_flat, dtype=float).reshape(len(MASSES), 2)
    accelerations = np.zeros_like(positions)

    for i in range(len(MASSES)):
        for j in range(len(MASSES)):
            if i == j:
                continue
            delta = positions[j] - positions[i]
            distance_squared = float(delta @ delta) + SOFTENING**2
            inv_distance_cubed = distance_squared ** (-1.5)
            accelerations[i] += G * MASSES[j] * delta * inv_distance_cubed

    return _flatten_positions(accelerations)


def simulate() -> tuple[np.ndarray, np.ndarray]:
    """Integrate the system with velocity-Verlet."""
    q0 = _flatten_positions(INITIAL_POSITIONS)
    v0 = _flatten_positions(INITIAL_VELOCITIES)
    times, states = velocity_verlet(
        acceleration=acceleration,
        t0=0.0,
        q0=q0,
        v0=v0,
        h=STEP,
        n_steps=N_STEPS,
    )
    return np.asarray(times, dtype=float), np.asarray(states, dtype=float)


def _body_trajectories(states: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    positions = states[:, : 2 * len(MASSES)].reshape(len(states), len(MASSES), 2)
    velocities = states[:, 2 * len(MASSES) :].reshape(len(states), len(MASSES), 2)
    return positions, velocities


def save_snapshot(
    times: np.ndarray, positions: np.ndarray, velocities: np.ndarray
) -> Path:
    """Save a static summary plot for the README."""
    fig = plt.figure(figsize=(11.5, 6.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0])
    ax_traj = fig.add_subplot(gs[0, 0])
    ax_speed = fig.add_subplot(gs[0, 1])

    colors = ["#4cc9f0", "#f72585", "#fca311"]
    labels = ["Body 1", "Body 2", "Body 3"]
    for index in range(len(MASSES)):
        ax_traj.plot(
            positions[:, index, 0],
            positions[:, index, 1],
            lw=1.0,
            color=colors[index],
            label=labels[index],
        )
        ax_traj.plot(
            positions[0, index, 0],
            positions[0, index, 1],
            marker="o",
            ms=5,
            color=colors[index],
        )

        speed = np.linalg.norm(velocities[:, index, :], axis=1)
        ax_speed.plot(times, speed, lw=1.1, color=colors[index], label=labels[index])

    ax_traj.set_title("Body trajectories")
    ax_traj.set_xlabel("x")
    ax_traj.set_ylabel("y")
    ax_traj.set_aspect("equal", adjustable="box")
    ax_traj.grid(True, alpha=0.3)
    ax_traj.legend(frameon=False)

    ax_speed.set_title("Speed over time")
    ax_speed.set_xlabel("t")
    ax_speed.set_ylabel("|v|")
    ax_speed.grid(True, alpha=0.3)
    ax_speed.legend(frameon=False)

    fig.suptitle("Three-body problem with velocity-Verlet")
    output_path = Path(__file__).with_name("three_body_problem.png")
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def save_animation(times: np.ndarray, positions: np.ndarray) -> Path:
    """Render a GIF animation with trails and live body markers."""
    frame_indices = np.linspace(1, len(times) - 1, N_FRAMES, dtype=int)
    frame_indices = np.unique(frame_indices)

    fig, ax = plt.subplots(figsize=(7.8, 7.2), constrained_layout=True)
    all_x = positions[:, :, 0]
    all_y = positions[:, :, 1]
    padding = 0.25
    x_min = float(all_x.min()) - padding
    x_max = float(all_x.max()) + padding
    y_min = float(all_y.min()) - padding
    y_max = float(all_y.max()) + padding

    ax.set_title("Planar three-body motion")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.grid(True, alpha=0.25)

    colors = ["#4cc9f0", "#f72585", "#fca311"]
    body_heads = []
    body_trails = []
    for index in range(len(MASSES)):
        (trail,) = ax.plot([], [], color=colors[index], lw=1.0, alpha=0.8)
        (line,) = ax.plot([], [], color=colors[index], lw=0.0, marker="o", ms=7)
        body_trails.append(trail)
        body_heads.append(line)

    info_text = ax.text(0.03, 0.96, "", transform=ax.transAxes)

    def update(frame_number: int) -> None:
        i = int(frame_indices[frame_number])
        for index in range(len(MASSES)):
            body_trails[index].set_data(
                positions[: i + 1, index, 0], positions[: i + 1, index, 1]
            )
            body_heads[index].set_data(
                [positions[i, index, 0]], [positions[i, index, 1]]
            )
        info_text.set_text(f"t = {times[i]:5.2f}")

    output_path = Path(__file__).with_name("three_body_problem.gif")
    frames: list[Image.Image] = []
    for frame_number in range(len(frame_indices)):
        update(frame_number)
        fig.canvas.draw()
        image = np.asarray(fig.canvas.buffer_rgba())
        frames.append(
            Image.fromarray(image).convert("P", palette=Image.ADAPTIVE, colors=256)
        )

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
    positions, velocities = _body_trajectories(states)
    save_snapshot(times, positions, velocities)
    animation_path = save_animation(times, positions)
    print(animation_path)


if __name__ == "__main__":
    main()
