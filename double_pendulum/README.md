# Double Pendulum Chaos Demo

This mini-project simulates a double pendulum with RK4 and exports both a static figure and an animated GIF.

## Install

Because this project imports `ode.solver`, install the RK4 package first:

```bash
cd ../runge_kutta_4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Then install this project's dependencies:

```bash
cd ../double_pendulum
python -m pip install -r requirements.txt
```

## Equations

State vector:

$$
y = (\theta_1, \omega_1, \theta_2, \omega_2).
$$

The system is

$$
\dot{\theta}_1 = \omega_1,\qquad
\dot{\theta}_2 = \omega_2
$$

and

$$
\dot{\omega}_1 =
\frac{
-g(2m_1+m_2)\sin\theta_1
-m_2g\sin(\theta_1-2\theta_2)
-2m_2\sin(\theta_1-\theta_2)\left(\omega_2^2l_2+\omega_1^2l_1\cos(\theta_1-\theta_2)\right)
}{
l_1\left(2m_1+m_2-m_2\cos(2\theta_1-2\theta_2)\right)
}
$$

$$
\dot{\omega}_2 =
\frac{
2\sin(\theta_1-\theta_2)\left(
\omega_1^2l_1(m_1+m_2)
+g(m_1+m_2)\cos\theta_1
+\omega_2^2l_2m_2\cos(\theta_1-\theta_2)
\right)
}{
l_2\left(2m_1+m_2-m_2\cos(2\theta_1-2\theta_2)\right)
}.
$$

Tiny initial-condition differences grow quickly, which is why the motion looks chaotic.

## Run

```bash
python double_pendulum.py
```

Outputs:

* `double_pendulum.png`
* `double_pendulum.gif`

![Double pendulum animation](double_pendulum.gif)
