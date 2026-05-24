from random import randint, random
import math as m

from opensimplex import OpenSimplex

SCALE_NOISE = 1/100
T_PERIOD = 0.5


class Slug:

    def __init__(self, x_init, y_init, speed):
        # Initial position
        self.x = x_init
        self.y = y_init

        self.speed = speed
        self.speed_factor = 1

        # Slime trail
        self.path = [(self.x, self.y)]

        self._noise = OpenSimplex(seed=randint(0, int(1e6)))

        self.dt_alive = 0
        self.dt_dead = 0

        self._dead = False
        self._phase = 2*m.pi*random()

    @property
    def dead(self):
        return self._dead

    def declare_dead(self):
        self._dead = True

    def move(self, dt=1):
        if self.dead:
            self.dt_dead += dt
            return

        self.dt_alive += dt

        vx, vy = self.velocity()
        self.x += vx*dt
        self.y += vy*dt

        self.path.append((self.x, self.y))

    def _heading(self):
        """
        Magnitude of 1
        """
        x_s = SCALE_NOISE*self.x
        y_s = SCALE_NOISE*self.y
        angle = 2*m.pi*self._noise.noise2d(x_s, y_s)
        return m.sin(angle), m.cos(angle)

    def velocity(self):
        hx, hy = self._heading()
        vx = abs(m.sin(2*m.pi*T_PERIOD*self.dt_alive + self._phase))*self.speed_factor*self.speed*hx
        vy = abs(m.sin(2*m.pi*T_PERIOD*self.dt_alive + self._phase))*self.speed_factor*self.speed*hy
        return vx, vy
