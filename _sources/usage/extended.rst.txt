======================
Extended functionality
======================

This document covers additional functionality that is provided by
ltapy.

Source apodization
------------------

The :mod:`apodization <ltapy.apodization>` module provides objects
for dealing with source apodization files.

It features a number of parser functions for reading surface, cylinder
or volume apodization file data into appropriate ``GridMesh`` objects.
These container objects store the grid mesh data and enable you to
export the data to e.g. a comma-separated values file.

.. note::

    Refer to the LightTools Help for more information on source
    apodization and apodization file formats (Illumination Module
    User's Guide > Chapter 2 Light Sources > Source Apodization).

For example, the following code creates a :class:`VolumeGridMesh
<ltapy.apodization.VolumeGridMesh>` object from three-dimensional mesh
data and data bounds:

    >>> import numpy as np
    >>> from ltapy.apodization import VolumeGridMesh
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

Write the grid mesh data to a volume apodization file:

    >>> vgmesh.write("volume_apodization.txt")

Read the volume apodization file into a ``VolumeGridMesh`` object:

    >>> from ltapy.apodization import read_vgmesh
    >>> vgmesh = read_vgmesh("volume_apodization.txt")
    >>> vgmesh.dim
    (3, 4, 2)

Write the grid mesh data to a comma-separated values (CSV) file:

    >>> vgmesh.to_csv("volume_apodization.csv")
