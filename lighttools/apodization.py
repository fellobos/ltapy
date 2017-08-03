"""
Objects for dealing with source apodization.

This module provides a number of objects useful for dealing with
source apodization and apodization files. It features a number of
parser functions for reading surface, cylinder or volume apodization
file data into appropriate GridMesh objects. These container objects
store the grid mesh data and enable data export to various file
formats (e.g. to a comma-separated values file).

Notes:
    Refer to the LightTools Help for more information on source
    apodization and apodization file formats (Illumination Module
    User's Guide > Chapter 2 Light Sources > Source Apodization).

Examples:
    Create a VolumeGridMesh object from three-dimensional mesh data
    and data bounds.

    >>> import numpy as np
    >>> values = np.array([
            [[1, 0, 7], [2, 1, 6], [4, 5 ,1], [1, 1, 6]],
            [[4, 5, 1], [1, 2, 3], [2, 2, 2], [1, 2, 3]],
        ])
    >>> bounds = (-1.5, 1.5, -2.0, 2.0, 0, 5)
    >>> vgmesh = VolumeGridMesh(values, bounds)
    >>> vgmesh.values
    array([[[1, 0, 7],
            [2, 1, 6],
            [4, 5, 1],
            [1, 1, 6]],

           [[4, 5, 1],
            [1, 2, 3],
            [2, 2, 2],
            [1, 2, 3]]])
    >>> vgmesh.bounds
    (-1.5, 1.5, -2.0, 2.0, 0, 5)
    >>> vgmesh.dim
    (3, 4, 2)

    Write the grid mesh data to a volume apodization file.

    >>> vgmesh.write("volume_apodization.txt")

    Read the volume apodization file into a VolumeGridMesh object.

    >>> vgmesh = read_vgmesh("volume_apodization.txt")
    >>> vgmesh.dim
    (3, 4, 2)

    Write the grid mesh data to a comma-separated values (CSV) file.

    >>> vgmesh.to_csv("volume_apodization.csv")
"""

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
    """
    Read surface apodization file into SurfaceGridMesh object.

    Args:
        filepath (str): Filepath of the surface apodization file.

    Returns:
        SurfaceGridMesh: A container object for interacting with the
            surface grid mesh data.
    """
    values, bounds = read_mesh(filepath, sghdparams)
    return SurfaceGridMesh(values, bounds)


def read_cgmesh(filepath):
    """
    Read cylinder apodization file into CylinderGridMesh object.

    Args:
        filepath (str): Filepath of the cylinder apodization file.

    Returns:
        CylinderGridMesh: A container object for interacting with the
            cylinder grid mesh data.
    """
    values, bounds = read_mesh(filepath, cghdparams)
    return CylinderGridMesh(values, bounds)


def read_vgmesh(filepath):
    """
    Read volume apodization file into VolumeGridMesh object.

    Args:
        filepath (str): Filepath of the volume apodization file.

    Returns:
        VolumeGridMesh: A container object for interacting with the volume
            grid mesh data.
    """
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
    return text.lower()  # ignore case


def parse(text):
    """
    Parse apodization file contents into logical sections.

    Apodization files consist of two sections: A header section followed
    by a data section. The mesh grid values in the data section are
    separated by whitespace and can be entered in free format. The header
    section has at least a single header line that starts with a keyword
    identifier (e.g. "mesh:", "xmin:", ...) followed by the associated
    data values.

    Args:
        text (str): Content of the apodization file.

    Returns:
        header (dict): Header section with each header line appearing as
            separate key:value pair.
        values (list): Data section with the mesh grid data values
            aggregated into a one-dimensional list.
    """
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
    """
    Generate a stream of tokens.

    Args:
        text (str): Content of the apodization file.

    Yields:
        str: Token
    """
    lexer = shlex.shlex(text)
    # Make sure that numbers are recognized correctly and that header
    # keywords can be identified by their trailing colon (e.g. "mesh:").
    lexer.wordchars += ".+-:"
    # Newline character is needed for parsing logic, don't skip!
    lexer.whitespace = lexer.whitespace.replace("\n", "")
    for token in lexer:
        yield token


def extract_header_info(header, hdparams):
    """
    Extract information from an apodization file header section.

    Args:
        header (dict): Header section with each header line appearing as
            separate key:value pair.
        hdparams (HeaderParams): Grid mesh header parameters.

    Returns:
        dim (tuple): Dimensions of the data set.
        bounds (tuple): Bounds of the data set.
    """
    if hdparams.type == GridType.SURFACE:
        for name in ("spheremesh", "polarmesh"):  # alternative mesh names
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
    """
    Reshape array to the given dimensions, ignoring extra data items.

    Args:
        values (list): Mesh grid data values as one-dimensional list.
        dim (tuple): Dimensions of the data set, e.g. (3, 2).

    Returns:
        numpy.ndarray: Mesh grid data values in new shape.
    """
    size = functools.reduce(lambda x, y: x*y, dim)
    return np.reshape(values[:size], dim[::-1]).astype(np.float)


class GridMesh:

    """
    Base class for container objects interacting with grid mesh data.
    """

    def __init__(self, values, bounds):
        self.values = values
        self.bounds = bounds

    @property
    def dim(self):
        return self.values.shape[::-1]

    def write(self, filepath, comment=""):
        """
        Write grid mesh data to an apodization file.

        Args:
            filepath (str): Filepath of the apodization file.
            comment (str, optional): Additional comment that appears at the
                beginning of the apodization file.
        """
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

    """
    Container object for interacting with surface grid mesh data.

    Store the grid mesh data required for surface apodization and enable
    data export to various file formats.

    Args:
        values (numpy.ndarray): Data values of the surface grid mesh given
            as two-dimensional array.
        bounds (tuple of floats, optional): Spatial or angular data set
            bounds given as (umin, vmin, umax, vmax).

    Attributes:
        values (numpy.ndarray): Data values of the surface grid mesh.
        bounds (tuple of floats): Spatial or angular data set bounds.
        dim (tuple of ints): Dimensions of the data set as (n, m) tuple,
            where n is the number of columns and m is the number of rows.

    Examples:
        Create a SurfaceGridMesh object from two-dimensional mesh data and
        (optional) data bounds.

        >>> import numpy as np
        >>> values = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        >>> bounds = (-1.0, -0.5, 1.0, 0.5)
        >>> sgmesh = SurfaceGridMesh(values, bounds)
        >>> sgmesh.values
        array([[ 1.,  2.,  3.],
               [ 4.,  5.,  6.]])
        >>> sgmesh.bounds
        (-1.0, -0.5, 1.0, 0.5)
        >>> sgmesh.dim
        (3, 2)

        Write the grid mesh data to a surface apodization file.

        >>> sgmesh.write("surface_apodization.txt")
    """

    hdparams = sghdparams

    def _write_header(self, filepath, comment):
        super()._write_header(filepath, comment)
        with open(filepath, "a") as f:
            f.write("{}: {:d} {:d}".format(self.hdparams.name, *self.dim))
            if self.bounds is not None:
                f.write(" {:g} {:g} {:g} {:g}".format(*self.bounds))
            f.write("\n")


    def to_csv(self, filepath, sort=False, ascending=False):
        """
        Write surface grid mesh data to a comma-separated values (CSV) file.

        Each line in the 3-column CSV file corresponds to a specific data
        value, with the xy-coordinates of the mesh grid midpoint in the first
        two columns and the data value itself in the third column.

        Data bounds must be specified because they are required for the
        calculation of the mesh grid midponts.

        Args:
            filepath (str): Filepath of the CSV file.
            sort (bool, optional): Numerically sort CSV file values along rows
                if sort is True. The default is False.
            ascending (bool, optional): The minimum value of V (vmin) is in
                the first row if ascending is True. The default is False.
                Refer to the LightTools Help (Section: Apodization Data
                Bounds) for an explanation how bounds are mapped to the data
                values.

        Raises:
            ValueError: If no data bounds are specified.
        """
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
 
    """
    Container object for interacting with cylinder grid mesh data.

    Store the grid mesh data required for cylinder apodization and enable
    data export to various file formats.

    Args:
        values (numpy.ndarray): Data values of the cylinder grid mesh
            given as two-dimensional array.
        bounds (tuple of floats): Radial and linear data set bounds given
            as (rmin, rmax, lmin, lmax).

    Attributes:
        values (numpy.ndarray): Data values of the cylinder grid mesh.
        bounds (tuple of floats): Radial and linear data set bounds.
        dim (tuple of ints): Dimensions of the data set as (n, m) tuple,
            where n is the number of columns and m is the number of rows.

    Examples:
        Create a CylinderGridMesh object from two-dimensional mesh data
        and data bounds.

        >>> import numpy as np
        >>> values = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        >>> bounds = (-1.0, -0.5, 1.0, 0.5)
        >>> cgmesh = CylinderGridMesh(values, bounds)
        >>> cgmesh.values
        array([[ 1.,  2.,  3.],
               [ 4.,  5.,  6.]])
        >>> cgmesh.bounds
        (-1.0, -0.5, 1.0, 0.5)
        >>> cgmesh.dim
        (3, 2)

        Write the grid mesh data to a cylinder apodization file.

        >>> cgmesh.write("cylinder_apodization.txt")
    """

    hdparams = cghdparams

    def _write_header(self, filepath, comment):
        super()._write_header(filepath, comment)
        with open(filepath, "a") as f:
            f.write("{}: {:d} {:d}\n".format(self.hdparams.name, *self.dim))
            for name, value in zip(self.hdparams.bounds, self.bounds):
                f.write("{}: {:g}\n".format(name, value))

    def to_csv(self, filepath, sort=False):
        """
        Write cylinder grid mesh data to a comma-separated values (CSV) file.

        Each line in the 3-column CSV file corresponds to a specific data
        value, with the radial and linear coordinates of the mesh grid
        midpoint in the first two columns and the data value itself in the
        third column.

        Args:
            filepath (str): Filepath of the CSV file.
            sort (bool, optional): Numerically sort CSV file values along rows
                if sort is True. The default is False.
        """
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
 
    """
    Container object for interacting with volume grid mesh data.

    Store the grid mesh data required for volume apodization and enable
    data export to various file formats.

    Args:
        values (numpy.ndarray): Data values of the volume grid mesh
            given as three-dimensional array.
        bounds (tuple of floats): Cartesian data set bounds in XYZ
            direction given as (xmin, xmax, ymin, ymax, zmin, zmax).

    Attributes:
        values (numpy.ndarray): Data values of the volume grid mesh.
        bounds (tuple of floats): Cartesian data set bounds in XYZ
            direction.
        dim (tuple of ints): Dimensions of the data set as (n, m, p)
            tuple, where n is the number of columns, m is the number of
            rows and p is the number of layers (xy matrices).

    Examples:
        Create a VolumeGridMesh object from three-dimensional mesh data
        and data bounds.

        >>> import numpy as np
        >>> values = np.array([
                [[1, 0, 7], [2, 1, 6], [4, 5 ,1], [1, 1, 6]],
                [[4, 5, 1], [1, 2, 3], [2, 2, 2], [1, 2, 3]],
            ])
        >>> bounds = (-1.5, 1.5, -2.0, 2.0, 0, 5)
        >>> vgmesh = VolumeGridMesh(values, bounds)
        >>> vgmesh.values
        array([[[1, 0, 7],
                [2, 1, 6],
                [4, 5, 1],
                [1, 1, 6]],

               [[4, 5, 1],
                [1, 2, 3],
                [2, 2, 2],
                [1, 2, 3]]])
        >>> vgmesh.bounds
        (-1.5, 1.5, -2.0, 2.0, 0, 5)
        >>> vgmesh.dim
        (3, 4, 2)

        Write the grid mesh data to a volume apodization file.

        >>> vgmesh.write("volume_apodization.txt")
    """


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
        """
        Write volume grid mesh data to a comma-separated values (CSV) file.

        Each line in the 4-column CSV file corresponds to a specific data
        value, with the xyz-coordinates of the mesh grid midpoint in the first
        three columns and the data value itself in the fourth column.

        Args:
            filepath (str): Filepath of the CSV file.
            sort (bool, optional): Numerically sort CSV file values along rows
                if sort is True. The default is False.
        """
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

    Args:
        num (int): Number of bin midpoints to generate. Must be positive.
        start (float): The starting value of the interval.
        stop (float): The end value of the interval.

    Returns:
        numpy.ndarray: num equally spaced bin midpoints in the interval
            [start, stop].

    Examples:
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
