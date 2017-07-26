import collections
import enum
import functools
import os
import shlex

import numpy as np


class GridType(enum.Enum):
    SURFACE = 1
    CYLINDER = 2
    VOLUME = 3


HeaderParams = collections.namedtuple(
    typename="HeaderParams",
    field_names=["type", "name", "dim", "bounds"],
)

sghdparams = HeaderParams(
    type=GridType.SURFACE,
    name="mesh",
    dim=("n", "m"),
    bounds=("umin", "vmin", "umax", "vmax"),
)

cghdparams = HeaderParams(
    type=GridType.CYLINDER,
    name="cylindermesh",
    dim=("n", "m"),
    bounds=("rmin", "rmax", "lmin", "lmax"),
)

vghdparams = HeaderParams(
    type=GridType.VOLUME,
    name="3dregulargridmesh",
    dim=("n", "m", "p"),
    bounds=("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"),
)


def read_sgmesh(filepath):
    values, bounds = read_mesh(filepath, sghdparams)
    return SurfaceGridMesh(values, bounds)


def read_cgmesh(filepath):
    values, bounds = read_mesh(filepath, cghdparams)
    return CylinderGridMesh(values, bounds)


def read_vgmesh(filepath):
    values, bounds = read_mesh(filepath, vghdparams)
    return VolumeGridMesh(values, bounds)


def read_mesh(filepath, hdparams):
    text = read(filepath)
    header, values = parse(text)
    dim, bounds = extract_header_info(header, hdparams)
    values = reshape(values, dim)
    return values, bounds


def read(filepath):
    with open(filepath) as f:
        text = f.read()
    return text.lower()


def parse(text):
    header, values = dict(), list()
    for token in tokenize(text):
        if token.endswith(":"):
            key = token.rstrip(":")
            container = header.setdefault(key, list())
            continue
        if token == "\n":
            container = values
            continue
        container.append(token)
    return header, values


def tokenize(text):
    lexer = shlex.shlex(text)
    lexer.wordchars += ".+-:"
    lexer.whitespace = lexer.whitespace.replace("\n", "")
    for token in lexer:
        yield token


def extract_header_info(header, hdparams):
    if hdparams.type == GridType.SURFACE:
        for name in ("spheremesh", "polarmesh"):
            if name in header:
                header[hdparams.name] = header.pop(name)
        n, m, *bounds = header[hdparams.name]
        dim = int(n), int(m)
        bounds = tuple(map(float, bounds)) if bounds else None
    else:  # GridType.CYLINDER or GridType.VOLUME
        dim = [int(x) for x in header[hdparams.name]]
        bounds = tuple(float(header[bound][0]) for bound in hdparams.bounds)
    return dim, bounds


def reshape(values, dim):
    size = functools.reduce(lambda x, y: x*y, dim)
    return np.reshape(values[:size], dim[::-1]).astype(np.float)


class GridMesh:

    def __init__(self, values, bounds):
        self.values = values
        self.bounds = bounds

    @property
    def dim(self):
        return self.values.shape[::-1]

    def write(self, filepath, comment=""):
        self._write_header(filepath, comment)
        self._write_data(filepath)

    def _write_header(self, filepath, comment):
        with open(filepath, "w") as f:
            if comment:
                f.write("{}\n".format(comment))

    def _write_data(self, filepath):
        with open(filepath, "ab") as f:
            np.savetxt(f, self.values, fmt="%g")


class SurfaceGridMesh(GridMesh):

    hdparams = sghdparams

    def _write_header(self, filepath, comment):
        super()._write_header(filepath, comment)
        with open(filepath, "a") as f:
            f.write("{}: {:d} {:d}".format(self.hdparams.name, *self.dim))
            if self.bounds is not None:
                f.write(" {:g} {:g} {:g} {:g}".format(*self.bounds))
            f.write("\n")


    def to_csv(self, filepath, sort=False, ascending=False):
        if self.bounds is None:
            msg = "Specify data bounds before exporting to CSV file"
            raise ValueError(msg)

        n, m = self.dim
        umin, vmin, umax, vmax = self.bounds

        xbins = binspace(n, umin, umax)
        ybins = binspace(m, vmax, vmin)
        if ascending:
            ybins = np.flipud(ybins)
        X, Y = np.meshgrid(xbins, ybins)
        data = np.stack(
            arrays=(X.flatten(), Y.flatten(), self.values.flatten()),
            axis=1
        )

        if sort:
            data.sort(axis=0)

        with open(filepath, "wb") as f:
            np.savetxt(f, data, fmt="%g", delimiter=",")


class CylinderGridMesh(GridMesh):

    hdparams = cghdparams

    def _write_header(self, filepath, comment):
        super()._write_header(filepath, comment)
        with open(filepath, "a") as f:
            f.write("{}: {:d} {:d}\n".format(self.hdparams.name, *self.dim))
            for name, value in zip(self.hdparams.bounds, self.bounds):
                f.write("{}: {:g}\n".format(name, value))

    def to_csv(self, filepath, sort=False):
        n, m = self.dim
        rmin, rmax, lmin, lmax = self.bounds

        xbins = binspace(n, rmin, rmax)
        ybins = binspace(m, lmin, lmax)
        X, Y = np.meshgrid(xbins, ybins)
        data = np.stack(
            arrays=(X.flatten(), Y.flatten(), self.values.flatten()),
            axis=1
        )

        if sort:
            data.sort(axis=0)

        with open(filepath, "wb") as f:
            np.savetxt(f, data, fmt="%g", delimiter=",")


class VolumeGridMesh(GridMesh):

    hdparams = vghdparams

    def _write_header(self, filepath, comment):
        super()._write_header(filepath, comment)
        with open(filepath, "a") as f:
            f.write(
                "{}: {:d} {:d} {:d}\n".format(self.hdparams.name, *self.dim)
            )
            for name, value in zip(self.hdparams.bounds, self.bounds):
                f.write("{}: {:g}\n".format(name, value))

    def to_csv(self, filepath, sort=False):
        n, m, p = self.dim
        xmin, xmax, ymin, ymax, zmin, zmax = self.bounds

        xbins = binspace(n, xmin, xmax)
        ybins = binspace(m, ymin, ymax)
        zbins = binspace(p, zmin, zmax)
        Z, Y, X = np.meshgrid(zbins, ybins, xbins, indexing='ij')
        data = np.stack(
            arrays=(
                X.flatten(), Y.flatten(), Z.flatten(), self.values.flatten()
            ),
            axis=1
        )

        if sort:
            data.sort(axis=0)

        with open(filepath, "wb") as f:
            np.savetxt(f, data, fmt="%g", delimiter=",")

    def _write_data(self, filepath):
        with open(filepath, "ab") as f:
            n, m, p = self.dim
            xmin, xmax, ymin, ymax, zmin, zmax = self.bounds
            zbins = binspace(p, zmin, zmax)
            for z, xymatrix in zip(zbins, self.values):
                f.write("# xy matrix for z = {:g}\n".format(z).encode())
                np.savetxt(f, xymatrix, fmt="%g")


def binspace(num, start, stop):
    """
    Return evenly spaced bin midpoints over the given interval.

    Calculate num evenly spaced bin midpoints over the closed interval
    [start, stop].

    Parameters
    ----------
    num : int
        Number of bin midpoints to generate. Must be positive.
    start : scalar
        The starting value of the interval.
    stop : scalar
        The end value of the interval.

    Returns
    -------
    numpy.ndarray
        num equally spaced bin midpoints in the interval [start, stop].

    Examples
    --------
    >>> bins = binspace(11, -1, 1)
    >>> bins
    array([ -9.09090909e-01,  -7.27272727e-01,  -5.45454545e-01,
            -3.63636364e-01,  -1.81818182e-01,   8.32667268e-17,
             1.81818182e-01,   3.63636364e-01,   5.45454545e-01,
             7.27272727e-01,   9.09090909e-01])
    """
    samples, step = np.linspace(start, stop, num+1, retstep=True)
    samples += 0.5 * step
    return samples[:-1]
