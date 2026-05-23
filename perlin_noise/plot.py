"""
Plot 2D Perlin noise
"""

from math import floor

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from perlin import perlin_noise, get_noise_2D, generate_gradient

FILE_NAME = 'perlin_noise_steps.png'

# ========== Grid ==========
max_coord = 3
d = 0.01
# d = 0.1
octaves = 1

# Grid coordinates
x_coords = y_coords = np.arange(0, max_coord, d)

# Get Perlin noise value for the 2D grid
# y-values: from max to min (top to bottom)
# y-values: From min to max (left to right)
grid = []
dot1 = []
for y in y_coords[::-1]:
    line = []
    line_dots = []
    for x in x_coords:
        line.append(perlin_noise(x, y, octaves))
        line_dots.append(abs(get_noise_2D(x, y)[1][0]))
    dot1.append(line_dots)
    grid.append(line)

grid = np.array(grid)
dot1 = np.array(dot1)

# ========== Plot ==========
linewidth = 0.75
linewidth_arrow = 5
show_coords = False

mpl.rcParams['axes.linewidth'] = linewidth
mpl.rcParams['image.cmap'] = 'Greys_r'
# mpl.rcParams['image.cmap'] = 'cividis_r'
# mpl.rcParams['image.cmap'] = 'bone_r'

fig = plt.figure(figsize=(6, 2), dpi=300)

def get_grid(num):
    ax = fig.add_subplot(num)
    ax.set_aspect('equal')
    ax.set_xlim(0, max_coord)
    ax.set_ylim(0, max_coord)
    # ax.set_xticks(list(range(0, max_coord+1)))
    # ax.set_yticks(list(range(0, max_coord+1)))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(axis='x', colors='black')
    ax.tick_params(axis='y', colors='black')
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(True, color='black', linewidth=linewidth)
    for c in range(0, max_coord+1):
        ax.plot((c, c), (0, max_coord), color='black', linewidth=linewidth)
        ax.plot((0, max_coord), (c, c), color='black', linewidth=linewidth)
    return ax

ax1 = get_grid(131)
ax2 = get_grid(132)
ax3 = get_grid(133)

d_coord = (0.4*max_coord, 0.75*max_coord)
g_xmin = floor(d_coord[0])
g_xmax = floor(d_coord[0]) + 1
g_ymin = floor(d_coord[1])
g_ymax = floor(d_coord[1]) + 1

for xg, yg in ((g_xmin, g_ymin), (g_xmax, g_ymin), (g_xmax, g_ymax), (g_xmin, g_ymax)):
    px = d_coord[0] - xg
    py = d_coord[1] - yg
    ax1.quiver(xg, yg, px, py, scale=1, color='blue', linewidth=linewidth_arrow, clip_on=False, scale_units='xy', linestyle=':')
ax1.scatter(*d_coord, marker='o', s=2, color='black')

for x in range(0, max_coord+1):
    for y in range(0, max_coord+1):
        gx, gy = generate_gradient(x, y)
        ax1.quiver(x, y, gx, gy, scale=2, color='red', linewidth=linewidth_arrow, clip_on=False, scale_units='xy')
        ax2.quiver(x, y, gx, gy, scale=2, color='red', linewidth=linewidth_arrow, clip_on=False, scale_units='xy')


ax2.imshow(dot1, extent=(0, max_coord, 0, max_coord))

ax3.imshow(grid, extent=(0, max_coord, 0, max_coord))

for ax, txt in zip((ax1, ax2, ax3), 'abc'):
    ax.text(max_coord/2, -0.4, f"({txt})",  size=8, weight='normal', horizontalalignment='center')

# plt.savefig(FILE_NAME, dpi=fig.dpi, metadata=None, bbox_inches='tight')
plt.savefig(FILE_NAME, dpi=fig.dpi, metadata=None)
# plt.show()

# ----------
# ----------
# ----------
from PIL import Image
img = Image.open(FILE_NAME)

# Coordinates
left = 200
top = 20
right = 1650
bottom = 600 - 20
img = img.crop(box=(left, top, right, bottom))
img.save(FILE_NAME)
# ----------
# ----------
# ----------



# # colormaps: https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html

# fig = plt.figure(figsize=(8, 8), edgecolor='black', linewidth=linewidth)

# ax = fig.add_subplot(111)
# ax.set_aspect('equal')

# # imshow: https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
# plt.imshow(grid, extent=(0, max_coord, 0, max_coord))
# plt.colorbar(orientation='vertical')

# ax.grid(True, color='black', linewidth=2)

# if show_coords:
#     plt.xticks(list(range(0, max_coord+1)), [i for i in range(0, max_coord+1)])
#     plt.yticks(list(range(0, max_coord+1)), [i for i in range(0, max_coord+1)])
# else:
#     plt.xticks(list(range(0, max_coord+1)), [None for i in range(0, max_coord+1)])
#     plt.yticks(list(range(0, max_coord+1)), [None for i in range(0, max_coord+1)])

# # Plot gradient vectors
# if octaves == 1:
#     for x in range(0, max_coord+1):
#         for y in range(0, max_coord+1):
#             gx, gy = generate_gradient(x, y)
#             plt.quiver(x, y, gx, gy, scale=5, color='red', linewidth=3, clip_on=False)

# plt.show()
