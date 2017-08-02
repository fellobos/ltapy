import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from lighttools.apodization import tokenize, read_sgmesh, read_vgmesh, read_cgmesh

PRECISION = 1e-06

tokenize_data = [
    # Test if comments are ignored (also inline comments).
    ("# comment\n1.0 2.2  # inline comment\n", 2),
    # Test if colon is accumulated into multi-character token.
    ("mesh: 2 3", 3),
    # Test if space, tab and linefeed characters are skipped.
    ("1.0 2.2\t0.2\r1.1", 4),
    # Test if newline is recognized as single-character token.
    ("1.0 2.2\n0.2", 4),
    # Test if integer and floating point numbers are correctly recognized.
    ("3 -4 +8 1.2 -2.3 +7.5 -1.3E+09 +1.2e-3", 8),
]


@pytest.mark.parametrize("text, count", tokenize_data)
def test_tokenize(text, count):
    tokens = []
    for token in tokenize(text):
        tokens.append(token)
    assert len(tokens) == count


sgmesh_1 = """\
# Surface grid mesh: w/o bounds
mesh: 3 2
1.0 2.0 3.0
4.0 5.0 6.0
"""

sgmesh_2 = """\
# Surface grid mesh: w/ bounds
mesh: 3 2 -1.0 -0.5 1.0 0.5
1.0 2.0 3.0
4.0 5.0 6.0
"""

sgmesh_3 = """\
# Surface grid mesh: upper case name
MESH: 3 2
1.0 2.0 3.0
4.0 5.0 6.0
"""

sgmesh_4 = """\
# Surface grid mesh: alternative mesh name
spheremesh: 3 2
1.0 2.0 3.0
4.0 5.0 6.0
"""

sgmesh_5 = """\
# Surface grid mesh: alternative mesh name
polarmesh: 3 2
1.0 2.0 3.0
4.0 5.0 6.0
"""

sgmesh_6 = """\
# Surface grid mesh: free format
mesh: 3 2
1.0 2.0
3.0
4.0
5.0 6.0
"""

sgmesh_7 = """\
# Surface grid mesh: too much data items
polarmesh: 3 2
1.0 2.0 3.0
4.0 5.0 6.0
7.0 8.0 9.0
"""

sgmesh_8 = """\
# Surface grid mesh: for read-write diff (floats must not have trailing zero)
mesh: 3 2
1.1 2.2 3.3
4.4 5.5 6.6
"""


@pytest.mark.parametrize("text, dim, bounds, size, mean", [
    (sgmesh_1, (3, 2), None, 6, 3.5),
    (sgmesh_2, (3, 2), (-1.0, -0.5, 1.0, 0.5), 6, 3.5),
    (sgmesh_3, (3, 2), None, 6, 3.5),
    (sgmesh_4, (3, 2), None, 6, 3.5),
    (sgmesh_5, (3, 2), None, 6, 3.5),
    (sgmesh_6, (3, 2), None, 6, 3.5),
    (sgmesh_7, (3, 2), None, 6, 3.5),
])
def test_sgmesh_read(text, dim, bounds, size, mean):
    f = write_tempfile(text)
    sgmesh = read_sgmesh(f.name)
    os.remove(f.name)
    assert sgmesh.dim == dim
    assert sgmesh.bounds == bounds
    assert sgmesh.values.size == size
    assert sgmesh.values.mean() == mean


def write_tempfile(text):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(text)
    return f


def test_sgmesh_write():
    f = write_tempfile(sgmesh_8)
    sgmesh = read_sgmesh(f.name)
    sgmesh.write(f.name, comment=sgmesh_8.split("\n")[0])
    with open(f.name) as f:
        assert f.read() == sgmesh_8
    os.remove(f.name)


def test_sgmesh_to_csv():
    f = write_tempfile(sgmesh_2)
    sgmesh = read_sgmesh(f.name)
    n, m = sgmesh.dim

    sgmesh.to_csv(f.name)
    df = pd.read_csv(f.name, names=["x", "y", "value"], header=None)
    assert df.value.min() == 1.0
    assert df.value.max() == 6.0
    assert df.value.mean() == 3.5
    i = 0
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(-6.66666667e-01, 0.25, 1.0),
        atol=PRECISION,
    )
    i = n - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(6.66666667e-01, 0.25, 3.0),
        atol=PRECISION,
    )
    i = (m-1) * n
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(-6.66666667e-01, -0.25, 4.0),
        atol=PRECISION,
    )
    i = n*m - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(6.66666667e-01, -0.25, 6.0),
        atol=PRECISION,
    )

    y = df.y
    sgmesh.to_csv(f.name, ascending=True)
    df = pd.read_csv(f.name, names=["x", "y", "value"], header=None)
    assert (df.y == np.flipud(y)).all()
    i = 0
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(-6.66666667e-01, -0.25, 1.0),
        atol=PRECISION,
    )
    i = (m-1) * n
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(-6.66666667e-01, 0.25, 4.0),
        atol=PRECISION,
    )

    os.remove(f.name)


cgmesh_1 = """\
# Cylinder grid mesh: for read-write diff (floats must not have trailing zero)
cylindermesh: 3 5
rmin: 1
rmax: 4
lmin: 0
lmax: 5
0.1 0.2 0.3
0.4 0.4 0.4
0.1 0.2 0.3
0.1 0.1 0.1
0.1 0.2 0.3
"""


def test_cgmesh_read():
    f = write_tempfile(cgmesh_1)
    cgmesh = read_cgmesh(f.name)
    os.remove(f.name)
    assert cgmesh.dim == (3, 5)
    assert cgmesh.bounds == (1, 4, 0, 5)
    assert cgmesh.values.size == 15
    assert cgmesh.values.mean() - 0.22000000000000003 < PRECISION


def test_cgmesh_write():
    f = write_tempfile(cgmesh_1)
    cgmesh = read_cgmesh(f.name)
    cgmesh.write(f.name, comment=cgmesh_1.split("\n")[0])
    with open(f.name) as f:
        assert f.read() == cgmesh_1
    os.remove(f.name)


def test_cgmesh_to_csv():
    f = write_tempfile(cgmesh_1)
    cgmesh = read_cgmesh(f.name)
    n, m = cgmesh.dim

    cgmesh.to_csv(f.name)
    df = pd.read_csv(f.name, names=["x", "y", "value"], header=None)
    assert df.value.min() == 0.1
    assert df.value.max() == 0.4
    assert df.value.mean() - 0.22000000000000003 < PRECISION
    i = 0
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(1.5, 0.5, 0.1),
        atol=PRECISION,
    )
    i = n - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(3.5, 0.5, 0.3),
        atol=PRECISION,
    )
    i = (m-1) * n
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(1.5, 4.5, 0.1),
        atol=PRECISION,
    )
    i = n*m - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.value[i]),
        b=(3.5, 4.5, 0.3),
        atol=PRECISION,
    )


vgmesh_1 = """\
# Volume grid mesh: for read-write diff (floats must not have trailing zero)
3dregulargridmesh: 3 4 5
xmin: -1.5
xmax: 1.5
ymin: -2
ymax: 2
zmin: 0
zmax: 5
# xy matrix for z = 0.5
1 0 7
2 1 6
4 5 1
1 1 6
# xy matrix for z = 1.5
4 5 1
1 2 3
2 2 2
1 2 3
# xy matrix for z = 2.5
1 8 9
4 5 1
1 2 3
1 2 3
# xy matrix for z = 3.5
5 5 0
5 0 5
5 5 6
3 1 5
# xy matrix for z = 4.5
2 2 2
8 6 6
2 2 2
1 6 6
"""


def test_vgmesh_read():
    f = write_tempfile(vgmesh_1)
    vgmesh = read_vgmesh(f.name)
    os.remove(f.name)
    assert vgmesh.dim == (3, 4, 5)
    assert vgmesh.bounds == (-1.5, 1.5, -2.0, 2.0, 0.0, 5.0)
    assert vgmesh.values.size == 60
    assert vgmesh.values.mean() - 3.2166666666666668 < PRECISION


def test_vgmesh_write():
    f = write_tempfile(vgmesh_1)
    vgmesh = read_vgmesh(f.name)
    vgmesh.write(f.name, comment=vgmesh_1.split("\n")[0])
    with open(f.name) as f:
        assert f.read() == vgmesh_1
    os.remove(f.name)


def test_vgmesh_to_csv():
    f = write_tempfile(vgmesh_1)
    vgmesh = read_vgmesh(f.name)

    vgmesh.to_csv(f.name)
    df = pd.read_csv(f.name, names=["x", "y", "z", "value"], header=None)
    assert df.value.mean() - vgmesh.values.mean() < 1e-6

    os.remove(f.name)


def test_vgmesh_to_csv():
    f = write_tempfile(vgmesh_1)
    vgmesh = read_vgmesh(f.name)
    n, m, p = vgmesh.dim

    vgmesh.to_csv(f.name)
    df = pd.read_csv(f.name, names=["x", "y", "z", "value"], header=None)
    assert df.value.min() == 0
    assert df.value.max() == 9
    assert df.value.mean() - 3.2166666666666668 < PRECISION
    i = 0
    assert np.allclose(
        a=(df.x[i], df.y[i], df.z[i], df.value[i]),
        b=(-1., -1.5, 0.5, 1),
        atol=PRECISION,
    )
    i = n - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.z[i], df.value[i]),
        b=(1., -1.5, 0.5, 7),
        atol=PRECISION,
    )
    i = (m-1) * n
    assert np.allclose(
        a=(df.x[i], df.y[i], df.z[i], df.value[i]),
        b=(-1., 1.5, 0.5, 1),
        atol=PRECISION,
    )
    i = n*m - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.z[i], df.value[i]),
        b=(1., 1.5, 0.5, 6),
        atol=PRECISION,
    )
    i = n*m*p - 1
    assert np.allclose(
        a=(df.x[i], df.y[i], df.z[i], df.value[i]),
        b=(1., 1.5, 4.5, 6),
        atol=PRECISION,
    )
