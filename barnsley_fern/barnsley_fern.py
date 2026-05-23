"""
Barnsley fern
https://en.wikipedia.org/wiki/Barnsley_fern
"""

import math
import random
random.seed(1729)

from matplotlib.patches import ConnectionPatch
import matplotlib as mpl
import matplotlib.pyplot as plt

orig_fern = True
rot_ang = math.radians(0)

if orig_fern:
    # Original Barnsley fern
    f1 = [    0,     0,     0, 0.16, 0,    0, 0.01]
    f2 = [ 0.85,  0.04, -0.04, 0.85, 0,  1.6, 0.86]
    f3 = [ 0.20, -0.26,  0.23, 0.22, 0,  1.6, 0.93]
    f4 = [-0.15,  0.28,  0.26, 0.24, 0, 0.44, 1.00]
else:
    f1 = [    0,     0,      0, 0.25,      0, -0.4, 0.02]
    f2 = [ 0.95, 0.005, -0.005, 0.93, -0.002,  0.5, 0.86]
    f3 = [0.035,  -0.2,   0.16, 0.04,  -0.09, 0.02, 0.93]
    f4 = [-0.04,   0.2,   0.16, 0.04,  0.083, 0.12, 1.00]


def transform(x, y):
    rand = random.uniform(0, 100)/100

    if rand < f1[6]:
        return f1[0]*x + f1[1]*y + f1[4], f1[2]*x + f1[3]*y + f1[5]
    elif f1[6] <= rand < f2[6]:
        return f2[0]*x + f2[1]*y + f2[4], f2[2]*x + f2[3]*y + f2[5]
    elif f2[6] <= rand < f3[6]:
        return f3[0]*x + f3[1]*y + f3[4], f3[2]*x + f3[3]*y + f3[5]
    else:
        return f4[0]*x + f4[1]*y + f4[4], f4[2]*x + f4[3]*y + f4[5]


def rotate(x, y, rot_ang):
    xR = math.cos(rot_ang)*x - math.sin(rot_ang)*y
    yR = math.sin(rot_ang)*x + math.cos(rot_ang)*y
    return xR, yR


def get_fern(n):
    """Return fern for n iterations"""

    x_all = [0]
    y_all = [0]
    for i in range(int(n)):
        x, y = transform(x_all[i], y_all[i])
        x_all.append(x)
        y_all.append(y)

    if rot_ang != 0:
        for i, (x, y) in enumerate(zip(x_all, y_all)):
            x, y = rotate(x, y, rot_ang)
            x_all[i] = x
            y_all[i] = y

    return x_all, y_all


def get_plot():
    leaf_color = '#27852d'
    frame_color = '#444444'
    linewidth = 0.5

    marker_lw = 0.1
    marker_size = 0.1
    marker = mpl.markers.MarkerStyle(marker='.', fillstyle='full')

    # Zoom box
    zx = (-0.1, 2.5)
    zy = (0.45, 3.55)

    mpl.rcParams['axes.linewidth'] = linewidth
    # mpl.rcParams['lines.markersize'] = 0.5
    # mpl.rcParams['scatter.marker'] = '.'
    # mpl.rcParams['scatter.edgecolors'] = 'face'
    # mpl.rcParams['figure.facecolor'] = 'black'

    # ax.set_facecolor('#e5b9a0')
    # ax.set_facecolor('#e5b8a1')
    # ax.invert_xaxis()

    # Figure
    inch_x = 8*(1/2.54)
    inch_y = 6*(1/2.54)
    fig = plt.figure(figsize=(inch_x,inch_y), dpi=300)
    fig.tight_layout()
    # fig.subplots_adjust(left=0.05, bottom=0.1, right=0.9, top=0.9, wspace=0, hspace=0)

    # Main image
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_aspect('equal')
    ax1.axis('off')
    x_all, y_all = get_fern(1e5)
    ax1.scatter(x_all, y_all, marker=marker, s=marker_size, c=leaf_color, linewidths=marker_lw)

    x = (zx[0], zx[1], zx[1], zx[0], zx[0])
    y = (zy[0], zy[0], zy[1], zy[1], zy[0])
    ax1.plot(x, y, c=frame_color, linewidth=linewidth)

    # Zoom box
    ax2 = fig.add_subplot(1, 2, 2)
    x_all, y_all = get_fern(1e6)
    ax2.scatter(x_all, y_all, marker=marker, s=marker_size, c=leaf_color, linewidths=marker_lw)
    ax2.set_xlim(*zx)
    ax2.set_ylim(*zy)
    ax2.set_aspect('equal')
    ax2.set_yticks([])
    ax2.set_xticks([])
    ax2.tick_params(axis='x', colors=frame_color)
    ax2.tick_params(axis='y', colors=frame_color)
    # ax2.axis('off')

    for xy in ((zx[0], zy[1]), (zx[1], zy[0])):
        con = ConnectionPatch(
                  xyA=xy,
                  xyB=xy,
                  coordsA="data",
                  coordsB="data",
                  axesA=ax2,
                  axesB=ax1,
                  color="red",
                  linewidth=linewidth,
        )
        ax2.add_artist(con)

    plt.savefig('barnsley_fern.png', dpi=fig.dpi, metadata=None, bbox_inches='tight')
    # plt.show()


if __name__ == '__main__':
    get_plot()

    from PIL import Image
    img = Image.open("barnsley_fern.png")

    # Coordinates
    left = 35
    top = 45
    right = 740
    bottom = 540
    img = img.crop(box=(left, top, right, bottom))
    img.save("barnsley_fern.png")

