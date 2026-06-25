"""Julia set renderer with zoom animation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm
from numba import njit, prange
from PIL import Image


@dataclass(frozen=True)
class ViewWindow:
    """Rectangular region in the complex plane."""

    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @property
    def extent(self) -> tuple[float, float, float, float]:
        return (self.xmin, self.xmax, self.ymin, self.ymax)


@njit(cache=True, parallel=True)
def julia_escape(
    width: int,
    height: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    c_re: float,
    c_im: float,
    max_iter: int,
) -> np.ndarray:
    """Compute smooth-escape Julia field for z -> z^2 + c."""
    escape_time = np.empty((height, width), dtype=np.float64)

    for y in prange(height):
        cy = ymin + (ymax - ymin) * y / (height - 1)
        for x in range(width):
            cx = xmin + (xmax - xmin) * x / (width - 1)
            zx = cx
            zy = cy
            i = 0

            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                mag2 = zx2 + zy2
                if mag2 > 4.0:
                    mag = np.sqrt(mag2)
                    escape_time[y, x] = i + 1 - np.log2(np.log(mag))
                    break

                zy = 2.0 * zx * zy + c_im
                zx = zx2 - zy2 + c_re
                i += 1
            else:
                escape_time[y, x] = max_iter

    return escape_time


def render_image(data: np.ndarray, view_window: ViewWindow, filename: Path) -> None:
    """Render one Julia image."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(
        data,
        cmap="twilight_shifted",
        origin="lower",
        extent=view_window.extent,
        aspect="equal",
        interpolation="bicubic",
        norm=PowerNorm(gamma=0.24),
    )
    ax.axis("off")
    fig.savefig(filename, dpi=280, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def make_zoom_frames(start: ViewWindow, end: ViewWindow, n_frames: int) -> list[ViewWindow]:
    """Build smooth zoom windows between two rectangles."""
    ts = np.linspace(0.0, 1.0, n_frames, dtype=float)
    eased = 3.0 * ts**2 - 2.0 * ts**3
    windows: list[ViewWindow] = []
    for t in eased:
        windows.append(
            ViewWindow(
                xmin=float((1.0 - t) * start.xmin + t * end.xmin),
                xmax=float((1.0 - t) * start.xmax + t * end.xmax),
                ymin=float((1.0 - t) * start.ymin + t * end.ymin),
                ymax=float((1.0 - t) * start.ymax + t * end.ymax),
            )
        )
    return windows


def save_zoom_animation(
    windows: list[ViewWindow],
    c_re: float,
    c_im: float,
    width: int,
    height: int,
    max_iter: int,
    output_path: Path,
) -> None:
    """Render a zoom animation gif."""
    fig, ax = plt.subplots(figsize=(7.8, 7.8), constrained_layout=True)
    ax.axis("off")

    first = julia_escape(
        width=width,
        height=height,
        xmin=windows[0].xmin,
        xmax=windows[0].xmax,
        ymin=windows[0].ymin,
        ymax=windows[0].ymax,
        c_re=c_re,
        c_im=c_im,
        max_iter=max_iter,
    )
    im = ax.imshow(
        first,
        cmap="twilight_shifted",
        origin="lower",
        interpolation="bicubic",
        norm=PowerNorm(gamma=0.24),
    )

    frames_rgb: list[Image.Image] = []
    for idx, window in enumerate(windows):
        data = julia_escape(
            width=width,
            height=height,
            xmin=window.xmin,
            xmax=window.xmax,
            ymin=window.ymin,
            ymax=window.ymax,
            c_re=c_re,
            c_im=c_im,
            max_iter=max_iter,
        )
        im.set_data(data)
        fig.canvas.draw()
        frame = np.asarray(fig.canvas.buffer_rgba())
        frames_rgb.append(Image.fromarray(frame).convert("RGB"))

    # Build a shared palette once to reduce inter-frame color flicker.
    palette_source = frames_rgb[len(frames_rgb) // 2].quantize(colors=256, method=Image.MEDIANCUT)
    frames: list[Image.Image] = []
    for frame_rgb in frames_rgb:
        frames.append(frame_rgb.quantize(palette=palette_source, dither=Image.FLOYDSTEINBERG))

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=32,
        loop=0,
        disposal=2,
        optimize=True,
    )
    plt.close(fig)


def main() -> None:
    width = 1400
    height = 1400
    max_iter = 1400

    c_re = -0.74543
    c_im = 0.11301

    overview = ViewWindow(xmin=-1.7, xmax=1.7, ymin=-1.7, ymax=1.7)
    zoom_target = ViewWindow(
        xmin=-0.7708,
        xmax=-0.7468,
        ymin=0.0910,
        ymax=0.1150,
    )

    overview_data = julia_escape(
        width=width,
        height=height,
        xmin=overview.xmin,
        xmax=overview.xmax,
        ymin=overview.ymin,
        ymax=overview.ymax,
        c_re=c_re,
        c_im=c_im,
        max_iter=max_iter,
    )
    zoom_data = julia_escape(
        width=width,
        height=height,
        xmin=zoom_target.xmin,
        xmax=zoom_target.xmax,
        ymin=zoom_target.ymin,
        ymax=zoom_target.ymax,
        c_re=c_re,
        c_im=c_im,
        max_iter=max_iter,
    )

    render_image(overview_data, overview, Path(__file__).with_name("julia_overview.png"))
    render_image(zoom_data, zoom_target, Path(__file__).with_name("julia_zoom.png"))

    windows = make_zoom_frames(overview, zoom_target, n_frames=180)
    save_zoom_animation(
        windows=windows,
        c_re=c_re,
        c_im=c_im,
        width=900,
        height=900,
        max_iter=max_iter,
        output_path=Path(__file__).with_name("julia_zoom.gif"),
    )
    print(Path(__file__).with_name("julia_zoom.gif"))


if __name__ == "__main__":
    main()
