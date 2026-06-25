# Reaction-Diffusion Art

This mini-project uses the Gray-Scott reaction-diffusion model to generate organic stripe-and-spot patterns.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Model

The Gray-Scott system evolves two concentration fields, \(U\) and \(V\):

$$
\frac{\partial U}{\partial t} = D_u \nabla^2 U - UV^2 + F(1-U)
$$

$$
\frac{\partial V}{\partial t} = D_v \nabla^2 V + UV^2 - (F + k)V
$$

where:

* \(D_u, D_v\) are diffusion rates,
* \(F\) is the feed rate,
* \(k\) is the kill rate.

Small parameter changes produce very different visual motifs.

## Run

```bash
python reaction_diffusion_art.py
```

Outputs:

* `reaction_diffusion_art.png`
* `reaction_diffusion_art.gif`

![Reaction-diffusion animation](reaction_diffusion_art.gif)

## Reference

* [Reaction–diffusion system, Wikipedia](https://en.wikipedia.org/wiki/Reaction%E2%80%93diffusion_system)
