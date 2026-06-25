"""Interactive Perlin flow field playground."""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame as pg


def smoothstep(t: float) -> float:
    return 6.0 * t**5 - 15.0 * t**4 + 10.0 * t**3


def lerp(t: float, a: float, b: float) -> float:
    return a + t * (b - a)


def gradient(ix: int, iy: int, seed: int) -> tuple[float, float]:
    # Deterministic integer hash -> angle in [0, 2pi).
    h = ix * 374761393 + iy * 668265263 + seed * 700001
    h = (h ^ (h >> 13)) * 1274126177
    h ^= h >> 16
    angle = (h & 0xFFFFFFFF) / 0xFFFFFFFF * (2.0 * math.pi)
    return math.cos(angle), math.sin(angle)


def perlin_2d(x: float, y: float, seed: int) -> float:
    x0 = math.floor(x)
    y0 = math.floor(y)
    x1 = x0 + 1
    y1 = y0 + 1

    gx0y0 = gradient(x0, y0, seed)
    gx0y1 = gradient(x0, y1, seed)
    gx1y0 = gradient(x1, y0, seed)
    gx1y1 = gradient(x1, y1, seed)

    dx0 = x - x0
    dx1 = x - x1
    dy0 = y - y0
    dy1 = y - y1

    d00 = gx0y0[0] * dx0 + gx0y0[1] * dy0
    d01 = gx0y1[0] * dx0 + gx0y1[1] * dy1
    d10 = gx1y0[0] * dx1 + gx1y0[1] * dy0
    d11 = gx1y1[0] * dx1 + gx1y1[1] * dy1

    sx = smoothstep(dx0)
    sy = smoothstep(dy0)
    nx0 = lerp(sx, d00, d10)
    nx1 = lerp(sx, d01, d11)
    return lerp(sy, nx0, nx1) / math.sqrt(2.0)


def fractal_perlin(x: float, y: float, seed: int, octaves: int = 3) -> float:
    value = 0.0
    amplitude = 1.0
    frequency = 1.0
    amp_sum = 0.0
    for _ in range(octaves):
        value += amplitude * perlin_2d(x * frequency, y * frequency, seed)
        amp_sum += amplitude
        amplitude *= 0.5
        frequency *= 2.0
    return value / amp_sum


@dataclass
class FlowField:
    scale: float
    drift: float
    seed: int

    def heading(self, x: float, y: float, t: float) -> tuple[float, float]:
        px = x * self.scale + self.drift * t
        py = y * self.scale
        n = fractal_perlin(px, py, self.seed)
        angle = 2.0 * math.pi * n
        return math.cos(angle), math.sin(angle)


@dataclass
class Particle:
    x: float
    y: float
    speed_scale: float
    hue: float


def spawn_particles(n: int, width: int, height: int, rng: random.Random) -> list[Particle]:
    particles: list[Particle] = []
    for _ in range(n):
        particles.append(
            Particle(
                x=rng.uniform(0, width),
                y=rng.uniform(0, height),
                speed_scale=rng.uniform(0.6, 1.4),
                hue=rng.uniform(165.0, 310.0),
            )
        )
    return particles


def make_color(hue: float) -> pg.Color:
    color = pg.Color(0, 0, 0)
    color.hsva = (hue % 360.0, 70.0, 100.0, 60.0)
    return color


def run(demo: bool = False, demo_seconds: float = 14.0) -> Path | None:
    pg.init()

    width, height = 1100, 700
    screen = pg.display.set_mode((width, height))
    pg.display.set_caption("Perlin Flow Playground")
    clock = pg.time.Clock()

    rng = random.Random(7)
    field = FlowField(scale=0.0075, drift=0.18, seed=137)
    particle_count = 950
    base_speed = 85.0
    particles = spawn_particles(particle_count, width, height, rng)

    trails = pg.Surface((width, height), flags=pg.SRCALPHA)
    fade = pg.Surface((width, height), flags=pg.SRCALPHA)
    fade.fill((0, 0, 0, 16))

    paused = False
    sim_time = 0.0
    screenshot = Path(__file__).with_name("perlin_flow_playground.png")
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        if demo:
            dt = 1.0 / 60.0

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_SPACE:
                    paused = not paused
                elif event.key == pg.K_r:
                    particles = spawn_particles(particle_count, width, height, rng)
                    trails.fill((0, 0, 0, 0))
                elif event.key == pg.K_c:
                    trails.fill((0, 0, 0, 0))
                elif event.key == pg.K_s:
                    pg.image.save(screen, screenshot)
                elif event.key == pg.K_UP:
                    base_speed = min(base_speed + 12.0, 260.0)
                elif event.key == pg.K_DOWN:
                    base_speed = max(base_speed - 12.0, 12.0)
                elif event.key == pg.K_RIGHT:
                    field.scale = min(field.scale + 0.0008, 0.03)
                elif event.key == pg.K_LEFT:
                    field.scale = max(field.scale - 0.0008, 0.001)
                elif event.key == pg.K_d:
                    field.drift = min(field.drift + 0.02, 1.0)
                elif event.key == pg.K_a:
                    field.drift = max(field.drift - 0.02, 0.0)

        if not paused:
            sim_time += dt
            trails.blit(fade, (0, 0))
            for p in particles:
                hx, hy = field.heading(p.x, p.y, sim_time)
                x_prev, y_prev = p.x, p.y
                speed = base_speed * p.speed_scale
                p.x = (p.x + hx * speed * dt) % width
                p.y = (p.y + hy * speed * dt) % height
                if abs(p.x - x_prev) < width * 0.5 and abs(p.y - y_prev) < height * 0.5:
                    pg.draw.aaline(trails, make_color(p.hue + sim_time * 12.0), (x_prev, y_prev), (p.x, p.y))

        screen.fill((8, 10, 15))
        screen.blit(trails, (0, 0))

        overlay = (
            "Controls: SPACE pause | UP/DOWN speed | LEFT/RIGHT scale | A/D drift | "
            "C clear | R respawn | S screenshot | ESC quit"
        )
        font = pg.font.SysFont("dejavusansmono", 18)
        text = font.render(overlay, True, (210, 220, 235))
        screen.blit(text, (18, 16))
        status = (
            f"speed={base_speed:.0f}  scale={field.scale:.4f}  drift={field.drift:.2f}  "
            f"particles={particle_count}"
        )
        status_text = font.render(status, True, (166, 190, 222))
        screen.blit(status_text, (18, 40))

        pg.display.flip()

        if demo and sim_time >= demo_seconds:
            pg.image.save(screen, screenshot)
            running = False

    pg.quit()
    return screenshot if demo else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Perlin Flow Playground")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run headless-style demo loop and save a screenshot.",
    )
    parser.add_argument(
        "--demo-seconds",
        type=float,
        default=14.0,
        help="Simulation duration used for --demo mode.",
    )
    args = parser.parse_args()
    output = run(demo=args.demo, demo_seconds=args.demo_seconds)
    if output is not None:
        print(output)


if __name__ == "__main__":
    main()
