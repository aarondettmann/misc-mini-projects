# Runge-Kutta 4 Solver

`ode` is a small Python package that provides a classical fourth-order
Runge-Kutta (RK4) ODE integrator implemented

1. as a C extension, and
2. as a concise, readable Numpy reference implementation.

Both RK4 solver implementations support scalar and vector-valued systems, and
are intended as a compact, readable reference implementations.

The function `rk4` is the default C-extension-backed solver. The Numpy
implementation with the same function signature is available as `rk4_numpy`:

```python
from ode.solver import rk4
from ode.solver import rk4_numpy
```

## Installation

```bash
python3 -m pip install -e ".[dev]"
pytest
```

## Examples

```python
from ode.solver import rk4

def rhs(t, y):
    """Exponential growth (first-order ODE)."""
    return y

times, states = rk4(rhs=rhs, t0=0.0, y0=1.0, h=0.001, n_steps=1000)

from math import e
print(states[-1] / e)  # 0.9999999999999925
```

Vector-valued states work the same way:

```python
from ode.solver import rk4

def rhs(_t, y):
    """Undamped harmonic oscillator (second-order ODE)."""
    x, v = y
    return (v, -x)

times, states = rk4(rhs=rhs, t0=0.0, y0=(1.0, 0.0), h=0.1, n_steps=10)
```

## Theory

The RK4 method solves an initial-value problem for an ordinary differential
equation,

$$
y'(t) = f(t, y), \qquad y(t_0) = y_0,
$$

by advancing the solution forward in fixed time steps. The solver implements
the classical fourth-order Runge-Kutta method:

It supports both a single scalar ODE and a vector-valued system of ODEs, as
long as `rhs(t, y)` returns the same shape as `y`.

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

[damped_oscillator_comparison.py](examples/damped_oscillator_comparison.py)
generates a comparison plot between the RK4 solution and the exact analytical
solution for an **underdamped harmonic oscillator**.

![RK4 vs exact damped oscillator](examples/rk4_vs_exact_damped_oscillator.png)

The left panel shows the displacement over time, and the right panel shows the
phase portrait. The RK4 trajectory closely matches the exact solution in both
views.

The phase portrait plots the system state variables against each other (here,
position versus velocity), instead of plotting them against time.
