"""Habitat geometry: planar heat-transfer surfaces and shape generators.

Conventions follow EnergyPlus: *tilt* is the angle between the outward normal and
the zenith (0 = roof facing up, 90 = wall, 180 = floor facing down); *azimuth* is the
outward-normal direction clockwise from north.  All generated shapes are convex, so no
exterior self-shading or exterior surface-to-surface radiation needs to be computed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List, Optional


@dataclass
class Surface:
    name: str
    construction: str
    area: float
    tilt: float
    azimuth: float
    perimeter: float
    centroid_height: float
    boundary: str = "outdoors"          # outdoors | ground | adiabatic
    view_sky: Optional[float] = None    # default (1+cos tilt)/2
    view_ground: Optional[float] = None
    char_length: Optional[float] = None

    @property
    def cos_tilt(self) -> float:
        return math.cos(math.radians(self.tilt))

    @property
    def F_sky(self) -> float:
        return self.view_sky if self.view_sky is not None else 0.5 * (1.0 + self.cos_tilt)

    @property
    def F_ground(self) -> float:
        return self.view_ground if self.view_ground is not None else 0.5 * (1.0 - self.cos_tilt)

    @property
    def length_vertical(self) -> float:
        return self.char_length or math.sqrt(self.area)

    @property
    def length_horizontal(self) -> float:
        return self.area / self.perimeter


@dataclass
class Geometry:
    surfaces: List[Surface]
    volume: float
    floor_area: float

    def by_name(self, name):
        return next(s for s in self.surfaces if s.name == name)


def box(length_x: float, width_y: float, height: float, wall: str, roof: str, floor: str,
        north_axis: float = 0.0, floor_boundary: str = "ground", z0: float = 0.0) -> Geometry:
    """Rectangular single-zone box; x runs east-west, y runs north-south."""
    L, W, H = length_x, width_y, height
    s = [
        Surface("wall_south", wall, L * H, 90.0, (180.0 + north_axis) % 360, 2 * (L + H), z0 + H / 2),
        Surface("wall_east", wall, W * H, 90.0, (90.0 + north_axis) % 360, 2 * (W + H), z0 + H / 2),
        Surface("wall_north", wall, L * H, 90.0, (0.0 + north_axis) % 360, 2 * (L + H), z0 + H / 2),
        Surface("wall_west", wall, W * H, 90.0, (270.0 + north_axis) % 360, 2 * (W + H), z0 + H / 2),
        Surface("roof", roof, L * W, 0.0, (180.0 + north_axis) % 360, 2 * (L + W), z0 + H),
        Surface("floor", floor, L * W, 180.0, (180.0 + north_axis) % 360, 2 * (L + W), z0, floor_boundary),
    ]
    return Geometry(s, L * W * H, L * W)


def vertical_cylinder(radius: float, height: float, wall: str, roof: str, floor: str,
                      n_facets: int = 12, floor_boundary: str = "ground", z0: float = 0.0) -> Geometry:
    """Vertical cylindrical module (e.g. a lander-derived habitat) approximated by facets."""
    side = 2 * radius * math.sin(math.pi / n_facets)
    s = []
    for i in range(n_facets):
        az = (i + 0.5) * 360.0 / n_facets
        s.append(Surface(f"wall_{i:02d}", wall, side * height, 90.0, az, 2 * (side + height), z0 + height / 2,
                         char_length=height))
    a_end = 0.5 * n_facets * radius ** 2 * math.sin(2 * math.pi / n_facets)
    s.append(Surface("roof", roof, a_end, 0.0, 180.0, n_facets * side, z0 + height, char_length=2 * radius))
    s.append(Surface("floor", floor, a_end, 180.0, 180.0, n_facets * side, z0, floor_boundary, char_length=2 * radius))
    return Geometry(s, a_end * height, a_end)


def horizontal_cylinder(radius: float, length: float, shell: str, end: str, floor: str,
                        axis_azimuth: float = 90.0, n_facets: int = 16, floor_width_frac: float = 0.8,
                        z0: float = 0.0) -> Geometry:
    """Horizontal cylindrical module lying on the surface (ISS-like / inflatable).

    The cylinder axis points toward ``axis_azimuth``.  The shell is split into
    ``n_facets`` strips around the circumference; the lower-most strips (tilt > 150 deg)
    are treated as resting on a regolith berm and given a *ground* boundary.
    The interior floor deck is not modelled separately (air zone = full cylinder).
    """
    s = []
    side = 2 * radius * math.sin(math.pi / n_facets)
    for i in range(n_facets):
        # angle of facet normal measured from vertical-up, sweeping across the axis
        theta = (i + 0.5) * 360.0 / n_facets
        tilt_signed = theta if theta <= 180 else 360 - theta
        az = (axis_azimuth + (90.0 if theta <= 180 else -90.0)) % 360
        zc = z0 + radius * (1 + math.cos(math.radians(theta)))
        boundary = "ground" if tilt_signed > 150 else "outdoors"
        cons = floor if boundary == "ground" else shell
        s.append(Surface(f"shell_{i:02d}", cons, side * length, tilt_signed, az, 2 * (side + length), zc,
                         boundary, char_length=2 * radius))
    a_end = 0.5 * n_facets * radius ** 2 * math.sin(2 * math.pi / n_facets)
    s.append(Surface("end_a", end, a_end, 90.0, axis_azimuth % 360, n_facets * side, z0 + radius, char_length=2 * radius))
    s.append(Surface("end_b", end, a_end, 90.0, (axis_azimuth + 180) % 360, n_facets * side, z0 + radius,
                     char_length=2 * radius))
    return Geometry(s, a_end * length, 2 * radius * floor_width_frac * length)


def dome(radius: float, shell: str, floor: str, n_az: int = 8, n_el: int = 3,
         floor_boundary: str = "ground") -> Geometry:
    """Hemispherical dome (e.g. regolith-covered 3D-printed shelter) as az x el facets."""
    s = []
    dphi = math.pi / 2 / n_el
    for j in range(n_el):
        phi0, phi1 = j * dphi, (j + 1) * dphi       # polar angle from zenith
        band = 2 * math.pi * radius ** 2 * (math.cos(phi0) - math.cos(phi1))
        tilt = math.degrees(0.5 * (phi0 + phi1))
        zc = radius * math.cos(0.5 * (phi0 + phi1))
        n = 1 if j == 0 and n_el > 2 else n_az
        for i in range(n):
            az = (i + 0.5) * 360.0 / n
            a = band / n
            per = 2 * math.sqrt(a) * 2
            s.append(Surface(f"dome_{j}_{i:02d}", shell, a, 0.0 if n == 1 else tilt, az, per, zc,
                             char_length=radius))
    a_floor = math.pi * radius ** 2
    s.append(Surface("floor", floor, a_floor, 180.0, 180.0, 2 * math.pi * radius, 0.0, floor_boundary,
                     char_length=2 * radius))
    return Geometry(s, 2.0 / 3.0 * math.pi * radius ** 3, a_floor)
