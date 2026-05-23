"""
Perlin noise function
"""

import math
from random import seed, uniform


def smoothstep(t):
    """
    Smooth curve with a zero derivative at 0 and 1, making it useful for interpolating
    """

    return 6*t**5 - 15*t**4 + 10*t**3


def lerp(t, a, b):
    """
    Linear interpolation between a and b, given a fraction t
    """

    return a + t*(b - a)


def generate_gradient(x, y):
    """
    Choose 'random' angle a and return normalised vector (cos(a), sin(a)).

    Same arguments x, y will return the same vector.
    """

    seed(a=(x*y + 0.5*x**3 + y))
    rand_ang = uniform(0, 2*math.pi)
    return (math.cos(rand_ang), math.sin(rand_ang))


def get_noise_2D(x, y):
    """
    Get plain noise for a single point, without taking into account either octaves or tiling.
    """

    # Grid point coordinates
    x_min = math.floor(x)
    y_min = math.floor(y)
    x_max = math.floor(x)+1
    y_max = math.floor(y)+1

    # Grid points
    #
    # gp1 ----- gp3
    #  |         |
    #  |         |
    #  |         |
    # gp0 ----- gp2
    gp0 = (x_min, y_min)
    gp1 = (x_min, y_max)
    gp2 = (x_max, y_min)
    gp3 = (x_max, y_max)

    # Gradient vectors
    gr0 = generate_gradient(*gp0)
    gr1 = generate_gradient(*gp1)
    gr2 = generate_gradient(*gp2)
    gr3 = generate_gradient(*gp3)

    # Collect dot products of each gradient vector times the point's distance
    # to the corresponding grid point. This gives the "influence" from each
    # gradient vector on the current point.

    # Compute dot product of (grid corner point to x, y) and (gradient vector).
    # The dot products give the "influence" from each gradient vector on the
    # current point (x, y).
    dots = []
    dots.append(gr0[0]*(x - gp0[0]) + gr0[1]*(y - gp0[1]))
    dots.append(gr1[0]*(x - gp1[0]) + gr1[1]*(y - gp1[1]))
    dots.append(gr2[0]*(x - gp2[0]) + gr2[1]*(y - gp2[1]))
    dots.append(gr3[0]*(x - gp3[0]) + gr3[1]*(y - gp3[1]))

    # Interpolate the data to get smooth variations
    sy = smoothstep(y - y_min)
    sx = smoothstep(x - x_min)

    # First, interpolation in y-direction (see grid point locations)
    noise = [
        lerp(sy, dots[0], dots[1]),
        lerp(sy, dots[2], dots[3]),
    ]
    # Second, interpolation in x-direction
    noise = lerp(sx, noise[0], noise[1])

    # Normalise to +/-1
    return noise/math.sqrt(2), dots  # ????? Scale factor okay?


def perlin_noise(x, y, octaves=1):
    """
    Return the Perlin noise value at a given point
    """

    pvalue = 0
    for o in range(octaves):
        o2 = 2**o  # 1, 2, 4, 8, ...
        pvalue += get_noise_2D(x*o2, y*o2)[0]/o2  # Every octave should have smaller amplitude

    # Need to scale n back down since adding all those extra octaves has
    # probably expanded it beyond ±1
    # 1 octave: ±1
    # 2 octaves: ±1½
    # 3 octaves: ±1¾
    pvalue /= (2 - 2**(1 - octaves))
    return pvalue
