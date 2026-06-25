# Lorenz Attractor

This mini-project simulates the Lorenz system with the shared RK4 solver and turns the result into a static plot and an animation.

![Lorenz attractor animation](lorenz_attractor.gif)

## Install

Because this project imports `ode.solver`, install the RK4 package first:

```bash
cd ../runge_kutta_4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Then install the Lorenz project dependencies:

```bash
cd ../lorenz_attractor
python -m pip install -r requirements.txt
```

## The equation

The Lorenz system is a three-variable model for chaotic flow:

$$
\begin{aligned}
\frac{dx}{dt} &= \sigma (y - x) \\
\frac{dy}{dt} &= x(\rho - z) - y \\
\frac{dz}{dt} &= xy - \beta z
\end{aligned}
$$

This project uses the classic parameter set

$$
\sigma = 10,\qquad \rho = 28,\qquad \beta = \frac{8}{3}.
$$

Starting from nearly identical initial conditions leads to very different long-term paths. That sensitivity is what makes the attractor feel alive in motion.

## Run

```bash
python lorenz_attractor.py
```

That writes:

* `lorenz_attractor.png`
* `lorenz_attractor.gif`

## What to look for

* The 3D trajectory spirals around two lobes.
* The moving point traces the current state.
* The time-series panel shows the x-coordinate evolving as the orbit folds through phase space.

## References

* [Lorenz system, Wikipedia](https://en.wikipedia.org/wiki/Lorenz_system)
* [Runge-Kutta methods, Wikipedia](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods)
