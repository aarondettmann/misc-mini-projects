#!/usr/bin/python3

# Version 1: 2024-04-26
# Updated:   2026-05-23

from random import random, choice
import itertools
import math

import drawsvg as draw
import numpy as np


def angle_pairs():
    yield (0,  60)
    yield (120, 180)
    yield (240, 300)


def ir_symbol_points(n_points, R1, R2, R3, include_center=True):
    """
    Create ionizing radiation symbol represented by random points

    n_points: approximate number of points
    R1: outer radius of inner source dot
    R2: inner radius of radiation
    R3: outer radius of radiation
    include_center: show or hide center point
    """

    # Area covered by points
    area_symbol = math.pi*(R3**2 - R2**2)/2
    area_symbol += math.pi*R1**2 if include_center else 0
    area_square = (2*R3)**2
    area_ratio = area_symbol/area_square

    # Number of points for symbol area
    n_points = math.ceil(n_points/area_ratio)

    # Random points in range [-1, 1)
    xy_rand = 2*np.random.random((n_points, 2)) - 1

    symbol_points = []
    for x, y in xy_rand:
        r = math.sqrt(x**2 + y**2)

        if include_center and (r < R1):
            symbol_points.append([x, y])

        if (R2 < r < R3):
            # Angle between 0 and 360 degrees
            ang = (math.degrees(math.atan2(y, x)) + 360) % 360

            for a1, a2 in angle_pairs():
                if (a1 < ang < a2):
                    symbol_points.append([x, y])

    return np.array(symbol_points)


def arc_points(n_points, radius, ang_start, ang_end):
    """
    Add evenly spaced points along a circular arc

    Args:
    n_points: Number of points along arc
    radius: arc radius
    ang_start: starting angle
    ang_end: end angle
    """

    points = []
    for i in range(n_points):
        ang_tot = ang_start - ang_end   # angle of arc
        ang_pnt = ang_tot/(n_points+1)  # angle in between points

        ang = math.radians(ang_start + ang_pnt*(1 + i))
        x = math.cos(ang)*radius
        y = math.sin(ang)*radius

        points.append(tuple((x, y)))

    return points


class CoverImage:

    def __init__(self, color_theme="bw", n_points=2000):
        self.color_theme = color_theme

        # ----- Defaults -----
        self.STROKE_WIDTH = 5e-3
        self.STROKE_WIDTH_THICKER = 1.5*5e-3
        self.STROKE_WIDTH_THICKEST = 3*5e-3
        self.NN_NODE_SIZE = 0.015

        # ----- Drawing size -----
        # Ionizing radiation symbol parameters
        self.R1 = 0.16
        self.R2 = 0.25
        self.R3 = 1.00

        self.x_size = 2*self.R3*1.01
        self.y_size = 2*self.R3*1.01

        # ----- Color theme -----
        if self.color_theme == "blue":
            self.COLOR_CANISTER = "white"
            self.COLOR_RADIATION = "white"
            self.COLOR_NETWORKS = "white"
            self.COLOR_NETWORKS_HIGHLIGHT = "white"
            self.bg_grad = self.radial_gradient(self.R3)

        elif self.color_theme == "bw":
            self.COLOR_CANISTER = "black"
            self.COLOR_RADIATION = "black"
            self.COLOR_NETWORKS = "black"
            self.COLOR_NETWORKS_HIGHLIGHT = "black"
            self.bg_grad = "white"

        else:
            raise ValueError(f"unsupported color theme '{color_theme}'")


        # ----- Other data -----
        self.symbol_points = ir_symbol_points(n_points, self.R1, self.R2, self.R3, include_center=False)
        self.symbol_points_animation = ir_symbol_points(n_points*1.5, self.R1, self.R2, self.R3, include_center=False)

    def radial_gradient(self, radius):
        grad = draw.RadialGradient(0, 0, radius)

        if self.color_theme == "blue":
            grad.add_stop(0, '#b3cde0', opacity=1)
            grad.add_stop(1, '#011f4b',  opacity=1)
            return grad

        # Inspired by Ceasium 137 glow
        if self.color_theme == "cs137":
            grad.add_stop(0, '#31eaff', opacity=0.8)
            grad.add_stop(0.7, '#4582ec', opacity=0.1)
            grad.add_stop(1, 'white',   opacity=0)
            return grad

        raise ValueError(f"unknown theme '{self.color_theme}'")

    def _create_background(self):
        dg_background = draw.Group(id="background")
        dg_background.append(draw.Rectangle(-self.x_size/2, -self.y_size/2, self.x_size, self.y_size, fill="white"))
        dg_background.append(draw.Circle(0, 0, self.R3, fill=self.bg_grad))
        self.d.append(dg_background)

    def _create_neural_networks(self):
        groups_nn = []
        for a1, a2, in angle_pairs():
            nn = {
                1: arc_points(2, self.R2 + 0.1*(self.R3-self.R2), a1, a2),
                2: arc_points(3, self.R2 + 0.5*(self.R3-self.R2), a1, a2),
                3: arc_points(5, self.R2 + 0.9*(self.R3-self.R2), a1, a2),
            }
            groups_nn.append(nn)

        dg_network = draw.Group(id="networks")
        for nn in groups_nn:
            filled_points = [choice(range(len(points))) for points in nn.values()]

            for layer_num, points in nn.items():
                filled_point = filled_points[layer_num-1]

                for i, (x, y) in enumerate(points):
                    if layer_num < len(nn.keys()):
                        k_next = layer_num+1
                        points_next = nn[k_next]
                        filled_point_next = filled_points[layer_num]

                        for j, (x_next, y_next) in enumerate(points_next):
                            stroke_width = self.STROKE_WIDTH
                            color = self.COLOR_NETWORKS
                            if (i == filled_point) and (j == filled_point_next):
                                stroke_width = self.STROKE_WIDTH_THICKER
                                color = self.COLOR_NETWORKS_HIGHLIGHT

                            paths_lines = draw.Group(stroke=color,
                                                     fill='none',
                                                     stroke_width=stroke_width)

                            p = draw.Path()
                            p.M(x, y).L(x_next, y_next)
                            paths_lines.append(p)

                            dg_network.append(paths_lines)

                    fill = self.COLOR_NETWORKS_HIGHLIGHT if (i == filled_point) else self.bg_grad
                    # fill = self.COLOR_NETWORKS_HIGHLIGHT if (i == filled_point) else self.COLOR_NETWORKS

                    stroke = self.COLOR_NETWORKS_HIGHLIGHT if (i == filled_point) else self.COLOR_NETWORKS
                    dg_network.append(draw.Circle(x, y, self.NN_NODE_SIZE,
                                      stroke="none", fill="white"))
                    dg_network.append(draw.Circle(x, y, self.NN_NODE_SIZE,
                                      stroke_width=self.STROKE_WIDTH,
                                      stroke=stroke, fill=fill))

        self.d.append(dg_network)

    def _create_ionizing_radiation_symbol(self):
        dg_symbol = draw.Group(id='ir_symbol')
        for x, y in self.symbol_points:
            r_circ = (self.R3 - math.sqrt(x**2 + y**2))*0.025
            r_circ *= random()
            circle = draw.Circle(x, y, r_circ, fill=self.COLOR_RADIATION)
            dg_symbol.append(circle)

        self.d.append(dg_symbol)

    def _create_ionizing_radiation_symbol_animated(self, t_end):
        dg_symbol = draw.Group(id='ir_symbol')
        for x, y in self.symbol_points_animation:
            r_circ = (self.R3 - math.sqrt(x**2 + y**2))*0.025
            r_circ *= random()

            t_show = random()*t_end
            drdt = -r_circ/t_end
            r_tend = r_circ + drdt*(t_end - t_show)

            circle = draw.Circle(x, y, t_end, fill=self.COLOR_RADIATION)
            circle.add_key_frame(0,      cx=x, cy=y, r=r_tend)
            circle.add_key_frame(t_show, cx=x, cy=y, r=0)
            circle.add_key_frame(t_show, cx=x, cy=y, r=r_circ)
            circle.add_key_frame(t_end,  cx=x, cy=y, r=r_tend)

            dg_symbol.append(circle)

        self.d.append(dg_symbol)

    def _create_fuel_cannister_cross_section(self):
        dg_cannister = draw.Group(id="cannister")
        r_cannister = self.R1*1.08
        dg_cannister.append(draw.Circle(0, 0, r_cannister,
                                        fill="none",
                                        stroke=self.COLOR_CANISTER,
                                        stroke_width=self.STROKE_WIDTH_THICKEST))

        # TODO: Better way than to use scale
        dg_slots = draw.Group(id="slots", transform='scale(0.8)')

        for i, j in itertools.product(range(4), repeat=2):
            if (i % 3 == 0) and (j % 3 == 0):
                continue

            L = (2*self.R1)/4.9
            spacing = 0.3*L
            rect = draw.Rectangle(-self.R1+(L+spacing)*i,
                                  -self.R1+(L+spacing)*j,
                                  L, L,
                                  # stroke=self.COLOR_CANISTER,
                                  # stroke_width=self.STROKE_WIDTH_THICKER,
                                  # fill="none",
                                  fill=self.COLOR_CANISTER,
                                  rx=L/5, ry=L/5, opacity=1)
            dg_slots.append(rect)

        dg_cannister.append(dg_slots)
        self.d.append(dg_cannister)

    def create_svg(self, filename):
        self.d = draw.Drawing(self.x_size, self.y_size,
                              origin="center", id_prefix="cover")

        self._create_background()

        # #  ####
        # for ang in [30, 90, 150]:
        #     self.d.append(draw.Ellipse(0, 0, self.R3, self.R2,
        #         stroke_width=self.STROKE_WIDTH_THICKEST*3,
        #         stroke='#f1f1f1', fill='none', transform=f'rotate({ang})'))
        # #  ####

        self._create_neural_networks()
        self._create_ionizing_radiation_symbol()
        self._create_fuel_cannister_cross_section()

        # Save file
        self.d.set_render_size(1400)
        print("creating svg image...")
        self.d.save_svg(filename)
        print("creating png image...")
        self.d.save_png(filename.replace(".svg", ".png"))

    def create_animation(self, filename, t_end=10):
        """
        Animation may require
        * CairoSVG
        * imageio
        """

        self.d = draw.Drawing(
                self.x_size, self.y_size,
                origin="center", id_prefix="cover",
                animation_config=
                draw.types.SyncedAnimationConfig(
                duration=t_end,
                show_playback_progress=False,
                show_playback_controls=False)
            )

        self._create_background()
        self._create_neural_networks()
        self._create_ionizing_radiation_symbol_animated(t_end)  # ===========
        self._create_fuel_cannister_cross_section()

        # Save file
        self.d.set_render_size(600)

        print("creating svg animation...")
        self.d.save_svg(filename)
        print("creating gif animation...")
        self.d.as_gif(filename.replace(".svg", ".gif"), fps=24)
        # self.d.as_mp4(filename.replace(".svg", ".mp4"), fps=30, verbose=True)


if __name__ == "__main__":
    cover_bw = CoverImage(color_theme="bw")
    cover_bw.create_svg("cover_bw.svg")

    cover_blue = CoverImage(color_theme="blue")
    cover_blue.create_svg("cover_blue.svg")

    # cover_blue.create_animation("cover_blue_animation.svg", t_end=20)
