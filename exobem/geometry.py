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
    is_internal_mass: bool = False      # sees every other surface (EnergyPlus InternalMass)
    curvature: Optional[tuple] = None   # ("cylinder" | "sphere", inner radius m): layers are curved shells
    vertices: Optional[list] = None     # optional 3-D polygon [(x, y, z), ...] in metres, for plotting

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
    c, sn = math.cos(math.radians(north_axis)), math.sin(math.radians(north_axis))

    def P(x, y, z):  # rotate clockwise by north_axis (x east, y north)
        return (x * c + y * sn, -x * sn + y * c, z)
    x0, x1, y0, y1, za, zb = -L / 2, L / 2, -W / 2, W / 2, z0, z0 + H
    polys = [
        [(x0, y0, za), (x1, y0, za), (x1, y0, zb), (x0, y0, zb)],
        [(x1, y0, za), (x1, y1, za), (x1, y1, zb), (x1, y0, zb)],
        [(x1, y1, za), (x0, y1, za), (x0, y1, zb), (x1, y1, zb)],
        [(x0, y1, za), (x0, y0, za), (x0, y0, zb), (x0, y1, zb)],
        [(x0, y0, zb), (x1, y0, zb), (x1, y1, zb), (x0, y1, zb)],
        [(x0, y0, za), (x0, y1, za), (x1, y1, za), (x1, y0, za)],
    ]
    for surf, poly in zip(s, polys):
        surf.vertices = [P(*v) for v in poly]
    return Geometry(s, L * W * H, L * W)


def vertical_cylinder(radius: float, height: float, wall: str, roof: str, floor: str,
                      n_facets: int = 12, floor_boundary: str = "ground", z0: float = 0.0) -> Geometry:
    """Vertical cylindrical module (e.g. a lander-derived habitat) approximated by facets."""
    side = 2 * radius * math.sin(math.pi / n_facets)
    s = []
    for i in range(n_facets):
        az = (i + 0.5) * 360.0 / n_facets
        s.append(Surface(f"wall_{i:02d}", wall, side * height, 90.0, az, 2 * (side + height), z0 + height / 2,
                         char_length=height, curvature=("cylinder", radius)))
    a_end = 0.5 * n_facets * radius ** 2 * math.sin(2 * math.pi / n_facets)
    s.append(Surface("roof", roof, a_end, 0.0, 180.0, n_facets * side, z0 + height, char_length=2 * radius))
    s.append(Surface("floor", floor, a_end, 180.0, 180.0, n_facets * side, z0, floor_boundary, char_length=2 * radius))
    ring = [(radius * math.sin(2 * math.pi * k / n_facets), radius * math.cos(2 * math.pi * k / n_facets))
            for k in range(n_facets + 1)]
    for i in range(n_facets):
        (xa, ya), (xb, yb) = ring[i], ring[i + 1]
        s[i].vertices = [(xa, ya, z0 + height), (xb, yb, z0 + height), (xb, yb, z0), (xa, ya, z0)]   # outward normal
    s[n_facets].vertices = [(x, y, z0 + height) for x, y in ring[:-1][::-1]]
    s[n_facets + 1].vertices = [(x, y, z0) for x, y in ring[:-1]]
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
                         boundary, char_length=2 * radius, curvature=("cylinder", radius)))
    a_end = 0.5 * n_facets * radius ** 2 * math.sin(2 * math.pi / n_facets)
    s.append(Surface("end_a", end, a_end, 90.0, axis_azimuth % 360, n_facets * side, z0 + radius, char_length=2 * radius))
    s.append(Surface("end_b", end, a_end, 90.0, (axis_azimuth + 180) % 360, n_facets * side, z0 + radius,
                     char_length=2 * radius))
    az = math.radians(axis_azimuth)
    ax_ = (math.sin(az), math.cos(az))                       # axis direction (x east, y north)
    pp = (math.sin(az + math.pi / 2), math.cos(az + math.pi / 2))   # horizontal normal for theta = 90 deg

    def ring_pt(theta, along):
        h = radius * math.sin(theta)
        return (along * ax_[0] + h * pp[0], along * ax_[1] + h * pp[1], z0 + radius + radius * math.cos(theta))
    for i in range(n_facets):
        t0, t1 = 2 * math.pi * i / n_facets, 2 * math.pi * (i + 1) / n_facets
        s[i].vertices = [ring_pt(t0, -length / 2), ring_pt(t1, -length / 2), ring_pt(t1, length / 2),
                         ring_pt(t0, length / 2)]
    s[n_facets].vertices = [ring_pt(2 * math.pi * k / n_facets, length / 2) for k in range(n_facets)]
    s[n_facets + 1].vertices = [ring_pt(2 * math.pi * k / n_facets, -length / 2) for k in range(n_facets)][::-1]
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
        n = n_az
        for i in range(n):
            az = (i + 0.5) * 360.0 / n
            a = band / n
            per = 2 * math.sqrt(a) * 2
            sf = Surface(f"dome_{j}_{i:02d}", shell, a, tilt, az, per, zc, char_length=radius,
                         curvature=("sphere", radius))

            def sph(phi, lam):
                return (radius * math.sin(phi) * math.sin(lam), radius * math.sin(phi) * math.cos(lam),
                        radius * math.cos(phi))
            if n == 1:
                sf.vertices = [sph(phi1, 2 * math.pi * k / 24) for k in range(24)][::-1]
            else:
                l0, l1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                sf.vertices = [sph(phi0, l0), sph(phi0, l1), sph(phi1, l1), sph(phi1, l0)]
            s.append(sf)
    a_floor = math.pi * radius ** 2
    s.append(Surface("floor", floor, a_floor, 180.0, 180.0, 2 * math.pi * radius, 0.0, floor_boundary,
                     char_length=2 * radius,
                     vertices=[(radius * math.sin(2 * math.pi * k / 48), radius * math.cos(2 * math.pi * k / 48), 0.0)
                               for k in range(48)]))
    return Geometry(s, 2.0 / 3.0 * math.pi * radius ** 3, a_floor)
