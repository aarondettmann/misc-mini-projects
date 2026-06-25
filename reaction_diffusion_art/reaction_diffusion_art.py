"""Gray-Scott reaction-diffusion art with PNG and GIF export."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


# Grid and numerical setup.
N = 260
DT = 1.0
WARMUP_STEPS = 4500
CAPTURE_STEPS = 5000
N_STEPS = WARMUP_STEPS + CAPTURE_STEPS

# Gray-Scott parameters (pattern-rich regime).
DU = 0.16
DV = 0.08
BASE_FEED = 0.034
BASE_KILL = 0.058

# Animation settings.
N_FRAMES = 260
FRAME_DURATION_MS = 45


def laplacian(field: np.ndarray) -> np.ndarray:
    """2D periodic Laplacian via stencil."""
    return (
        -field
        + 0.20 * (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0))
        + 0.20 * (np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1))
        + 0.05
        * (
            np.roll(np.roll(field, 1, axis=0), 1, axis=1)
            + np.roll(np.roll(field, 1, axis=0), -1, axis=1)
            + np.roll(np.roll(field, -1, axis=0), 1, axis=1)
            + np.roll(np.roll(field, -1, axis=0), -1, axis=1)
        )
    )


def initialize_state() -> tuple[np.ndarray, np.ndarray]:
    """Initialize U and V concentrations."""
    u = np.ones((N, N), dtype=float)
    v = np.zeros((N, N), dtype=float)

    rng = np.random.default_rng(7)

    yy, xx = np.ogrid[:N, :N]
    for _ in range(26):
        cx = int(rng.integers(15, N - 15))
        cy = int(rng.integers(15, N - 15))
        radius = float(rng.uniform(6.0, 20.0))
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
        u[mask] = 0.45 + 0.10 * rng.random()
        v[mask] = 0.18 + 0.16 * rng.random()

    # Extra central disturbance to trigger strong interactions.
    c = N // 2
    radius_center = 24
    center_mask = (xx - c) ** 2 + (yy - c) ** 2 <= radius_center**2
    u[center_mask] = 0.35
    v[center_mask] = 0.30

    u += 0.025 * (rng.random((N, N)) - 0.5)
    v += 0.020 * (rng.random((N, N)) - 0.5)
    return np.clip(u, 0.0, 1.0), np.clip(v, 0.0, 1.0)


def parameter_fields() -> tuple[np.ndarray, np.ndarray]:
    """Create mildly spatially varying feed/kill fields."""
    y = np.linspace(0.0, 1.0, N, dtype=float)
    x = np.linspace(0.0, 1.0, N, dtype=float)
    xx, yy = np.meshgrid(x, y)
    feed = (
        BASE_FEED
        + 0.006 * np.sin(2.0 * np.pi * xx)
        + 0.004 * np.cos(2.0 * np.pi * yy)
        + 0.003 * np.sin(2.0 * np.pi * (xx + yy))
    )
    kill = (
        BASE_KILL
        + 0.003 * np.cos(2.0 * np.pi * xx)
        - 0.002 * np.sin(2.0 * np.pi * yy)
        + 0.002 * np.cos(2.0 * np.pi * (xx - yy))
    )
    return np.clip(feed, 0.018, 0.085), np.clip(kill, 0.040, 0.078)


def render_field(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Return a derived field with stronger visual structure than raw V."""
    return v * (1.0 - u)


def simulate() -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """Run Gray-Scott integration and collect animation frames."""
    u, v = initialize_state()
    feed, kill = parameter_fields()
    frames: list[np.ndarray] = []

    frame_steps = np.linspace(WARMUP_STEPS, N_STEPS - 1, N_FRAMES, dtype=int)
    frame_set = set(frame_steps.tolist())

    for step in range(N_STEPS):
        lu = laplacian(u)
        lv = laplacian(v)
        uvv = u * v * v

        u += (DU * lu - uvv + feed * (1.0 - u)) * DT
        v += (DV * lv + uvv - (feed + kill) * v) * DT
        np.clip(u, 0.0, 1.0, out=u)
        np.clip(v, 0.0, 1.0, out=v)

        if step >= WARMUP_STEPS and step in frame_set:
            frames.append(render_field(u, v).copy())

    return u, v, frames


def save_snapshot(u: np.ndarray, v: np.ndarray) -> Path:
    """Save a static summary image."""
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8), constrained_layout=True)
    ax_pattern, ax_profile = axes

    field = render_field(u, v)
    p_low, p_high = np.percentile(field, [2.0, 98.0])
    image = ax_pattern.imshow(
        field,
        cmap="magma",
        interpolation="bilinear",
        vmin=float(p_low),
        vmax=float(p_high),
    )
    ax_pattern.set_title("Derived texture field  V(1-U)")
    ax_pattern.set_xticks([])
    ax_pattern.set_yticks([])
    fig.colorbar(image, ax=ax_pattern, fraction=0.046, pad=0.04)

    center_line = field[field.shape[0] // 2, :]
    ax_profile.plot(center_line, color="#4cc9f0", lw=1.4)
    ax_profile.set_title("Center-line concentration profile")
    ax_profile.set_xlabel("x index")
    ax_profile.set_ylabel("V(1-U)")
    ax_profile.grid(True, alpha=0.3)

    fig.suptitle("Gray-Scott reaction-diffusion pattern")
    output = Path(__file__).with_name("reaction_diffusion_art.png")
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def save_animation(frames: list[np.ndarray]) -> Path:
    """Save animation GIF from collected V-field frames."""
    fig, ax = plt.subplots(figsize=(6.5, 6.5), constrained_layout=True)
    all_values = np.concatenate([frame.ravel() for frame in frames])
    p_low, p_high = np.percentile(all_values, [2.0, 98.0])
    im = ax.imshow(
        frames[0],
        cmap="magma",
        interpolation="bilinear",
        vmin=float(p_low),
        vmax=float(p_high),
    )
    ax.set_title("Gray-Scott reaction-diffusion")
    ax.set_xticks([])
    ax.set_yticks([])
    text = ax.text(
        0.03,
        0.96,
        "",
        color="white",
        transform=ax.transAxes,
        va="top",
    )

    gif_frames: list[Image.Image] = []
    total = len(frames)
    for idx, frame in enumerate(frames):
        im.set_data(frame)
        text.set_text(
            f"step ~ {WARMUP_STEPS + int((idx / max(1, total - 1)) * CAPTURE_STEPS):5d}\n"
            f"F≈{BASE_FEED:.3f}, k≈{BASE_KILL:.3f}"
        )
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())
        gif_frames.append(Image.fromarray(buf).convert("P", palette=Image.ADAPTIVE, colors=256))

    output = Path(__file__).with_name("reaction_diffusion_art.gif")
    gif_frames[0].save(
        output,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=False,
    )
    plt.close(fig)
    return output


def main() -> None:
    u, v, frames = simulate()
    save_snapshot(u, v)
    gif_path = save_animation(frames)
    print(gif_path)


if __name__ == "__main__":
    main()
