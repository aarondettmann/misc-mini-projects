# misc-mini-project

A collection of small, miscellaneous code snippets and experiments.

## Installation

Each mini project has its own `requirements.txt` inside its folder.

To install dependencies for one project:

```bash
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Projects

### Barnsley Fern

* **Files:** [barnsely_fern](barnsley_fern).
* **References:** [Barnsly fern, Wikipedia](https://en.wikipedia.org/wiki/Barnsley_fern)

![Barnsley fern](barnsley_fern/barnsley_fern.png)

### Mandelbrot Set

* **Files:** [mandelbrot_set](mandelbrot_set).
* **References:** [Mandelbrot set, Wikipedia](https://en.wikipedia.org/wiki/Mandelbrot_set)

| ![Overview](mandelbrot_set/mandelbrot_overview.png) | ![Seahorse](mandelbrot_set/mandelbrot_seahorse.png) |
| --- | --- | 

### Perlin Noise

* **Files:** [perlin_noise](perlin_noise).
* **References:** [Perlin noise, Wikipedia](https://en.wikipedia.org/wiki/Perlin_noise)

![Perlin noise generation](perlin_noise/perlin_noise_steps.png)

### Perlin Flow Playground

* **Files:** [perlin_flow_playground](perlin_flow_playground).
* **References:** [Perlin noise, Wikipedia](https://en.wikipedia.org/wiki/Perlin_noise)

![Perlin flow playground](perlin_flow_playground/perlin_flow_playground.png)

### Ionizing Radiation Art

* **Files:** [ionizing_radiation_art](ionizing_radiation_art).

![Ionizing raditaion art](ionizing_radiation_art/cover_blue_animation.svg)

### Runge-Kutta 4 Solver

* **Files:** [runge_kutta_4](runge_kutta_4).
* **References:** [Runge-Kutta methods, Wikipedia](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods)

![Underdamped oscillator comparison](runge_kutta_4/examples/rk4_vs_exact_damped_oscillator.png)

### Lorenz Attractor

* **Files:** [lorenz_attractor](lorenz_attractor).
* **References:** [Lorenz system, Wikipedia](https://en.wikipedia.org/wiki/Lorenz_system)

![Lorenz attractor](lorenz_attractor/lorenz_attractor.gif)

### Deadly Slugs

* **Files:** [deadly_slugs](deadly_slugs).

| ![Screenshot 1](deadly_slugs/screenshots/01.png) | ![Screenshot 2](deadly_slugs/screenshots/02.png) |
| --- | --- | 

### Plane Rotation using Complex Numbers

* **Files:** [plane_rotation](plane_rotation).

![Plane Rotation](plane_rotation/example.gif)

## Idea

Future mini-projects that fit this repo well:

* **Julia Set Zoomer** — reuse the Mandelbrot renderer pattern for a Julia-set companion.
* **Lorenz Attractor with RK4** — show chaos with a clean RK4-based ODE simulation and animation.
* **Reaction-Diffusion Art** — generate organic Gray-Scott textures and pattern evolution.
* **Double Pendulum Chaos Demo** — visualize chaotic motion with phase portraits and trails.

## Copyright

Copyright Aaron Dettmann.
