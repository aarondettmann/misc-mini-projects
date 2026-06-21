"""
Mandelbrot fractal renderer for escape-time visualizations of the Mandelbrot
set over arbitrary regions of the complex plane.

Version 1: 2020
Updated:   2026
"""

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm
from numba import njit, prange


@dataclass(frozen=True)
class ViewWindow:
    """
    Rectangular region of the complex plane,
    defining the area to render.
    """

    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @property
    def extent(self) -> tuple[float, float, float, float]:
        return (self.xmin, self.xmax, self.ymin, self.ymax)


# ----- Core -----

@njit(cache=True, parallel=True)
def mandelbrot_escape(
    width: int,
    height: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    max_iter: int,
) -> np.ndarray:
    """
    Compute smooth escape-time Mandelbrot fractal (core Mandelbrot kernel).

    Notes:
        - Using Numba for performance.

    Output:
        2D array (height x width) of escape-time values.
    """

    # Number of iterations until the function exceeds the divergence threshold
    escape_time = np.empty((height, width), dtype=np.float64)

    # Parallelize over rows (each row independent)
    for y in prange(height):
        cy = ymin + (ymax - ymin) * y / (height - 1)

        for x in range(width):
            cx = xmin + (xmax - xmin) * x / (width - 1)

            # z = 0 in complex plane
            zr = 0.0
            zi = 0.0

            i = 0

            # Iterate z -> z^2 + c
            while i < max_iter:
                zr2 = zr * zr
                zi2 = zi * zi

                mag2 = zr2 + zi2  # |z|^2

                # Escape condition
                if mag2 > 4.0:
                    mag = np.sqrt(mag2)

                    # Smooth coloring (continuous escape time)
                    escape_time[y, x] = i + 1 - np.log2(np.log(mag))
                    break

                # Complex multiplication: z^2 + c
                zi = 2.0 * zr * zi + cy
                zr = zr2 - zi2 + cx

                i += 1

            else:
                # Point never escaped
                escape_time[y, x] = max_iter

    return escape_time


# ----- Rendering -----

def render(
    data: np.ndarray,
    view_window: ViewWindow,
    filename: str,
    *,
    cmap: str = "twilight_shifted",
) -> None:
    """Render escape-time field and save to file."""

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.imshow(
        data,
        cmap=cmap,
        origin="lower",
        extent=view_window.extent,
        aspect="equal",
        interpolation="bicubic",
        norm=PowerNorm(gamma=0.3),  # improves visual contrast in deep regions
    )

    ax.axis("off")

    fig.savefig(
        filename,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
    )

    plt.close(fig)


# ----- High-level function -----

def generate_image(
    view_window: ViewWindow,
    filename: str,
    *,
    width: int,
    height: int,
    max_iter: int,
) -> None:
    """
    Compute and render one Mandelbrot image.
    """

    print(f"Rendering {filename}...")

    data = mandelbrot_escape(
        width=width,
        height=height,
        xmin=view_window.xmin,
        xmax=view_window.xmax,
        ymin=view_window.ymin,
        ymax=view_window.ymax,
        max_iter=max_iter,
    )

    render(data, view_window, filename)

    print(f"Saved {filename}")


def main() -> None:
    width = 2000
    height = 2000
    max_iter = 1000

    # Full fractal view
    overview = ViewWindow(
        xmin=-2.0,
        xmax=1.0,
        ymin=-1.5,
        ymax=1.5,
    )

    # Seahorse region
    # Recreates: https://en.wikipedia.org/wiki/File:Mandel_zoom_03_seehorse.jpg
    seahorse = ViewWindow(
        xmin=-0.751085,
        xmax=-0.734975,
        ymin=0.118378,
        ymax=0.134488,
    )

    generate_image(
        overview,
        "mandelbrot_overview.png",
        width=width,
        height=height,
        max_iter=max_iter,
    )

    generate_image(
        seahorse,
        "mandelbrot_seahorse.png",
        width=width,
        height=height,
        max_iter=max_iter,
    )


if __name__ == "__main__":
    main()
