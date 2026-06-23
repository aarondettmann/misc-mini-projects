# Runge-Kutta 4 Solver

`ode` is a small Python package that exposes a classical fourth-order Runge-Kutta (RK4) ODE integrator backed by a C extension. It supports scalar initial values and vector-valued systems, and is intended as a compact, readable reference implementation.

## Quick start

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

## Usage

```python
from ode.solver import rk4

def rhs(t, y):
    return y

times, states = rk4(rhs=rhs, t0=0.0, y0=1.0, h=0.1, n_steps=10)
```

Vector-valued states work the same way:

```python
def rhs(_t, y):
    x, v = y
    return (v, -x)

times, states = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.1, n_steps=10)
```

## Theory

The RK4 method solves an initial-value problem for an ordinary differential equation,

$$
y'(t) = f(t, y), \qquad y(t_0) = y_0,
$$

by advancing the solution forward in fixed time steps. This solver implements the classical fourth-order Runge-Kutta method:

It supports both a single scalar ODE and a vector-valued system of ODEs, as long as `rhs(t, y)` returns the same shape as `y`.

$$
\begin{aligned}
k_1 &= f(t_n, y_n) \\
k_2 &= f\left(t_n + \frac{h}{2}, y_n + \frac{h}{2}k_1\right) \\
k_3 &= f\left(t_n + \frac{h}{2}, y_n + \frac{h}{2}k_2\right) \\
k_4 &= f(t_n + h, y_n + hk_3) \\
\\
y_{n+1} &= y_n + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4)
\end{aligned}
$$

* **References:** [Runge-Kutta methods, Wikipedia](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods)

## Example

`examples/damped_oscillator_comparison.py` generates a comparison plot between the RK4 solution and the exact analytical solution for an underdamped harmonic oscillator.

![RK4 vs exact damped oscillator](examples/rk4_vs_exact_damped_oscillator.png)

The left panel shows the displacement over time, and the right panel shows the phase portrait. The RK4 trajectory closely matches the exact solution in both views.

A phase portrait plots the system state variables against each other, such as position versus velocity, instead of plotting them against time.
