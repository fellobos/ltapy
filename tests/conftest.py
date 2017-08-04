import os

import pytest

from lighttools import session
from lighttools import vslogger as vsl


@pytest.fixture(scope="class")
def vslogger(request):
    interactive, lt = setup(request)

    open_file(lt, "vslogger.lts")
    key = (
        "SOLID[Phosphor].VOLUME_INTERFACE[VolumeInterface_EOS]"
        ".VOLUME_SCATTER_LOG[VolumeScatterLog]"
    )
    vslogger = vsl.VolumeScatterLogger(lt, key)

    teardown(interactive, lt, request)

    return vslogger


def setup(request):
    # For interactive testing the LightTools PID can be passed
    # via the command line, e.g. py.test --pid=1234.
    pid = request.config.getoption("--pid")
    interactive = True if pid else False

    # Connect to a running LightTools session or create a new one.
    if interactive:
        ses = session.Session(pid)
    else:
        ses = session.Session.new()

    return interactive, ses.ltapi


def pytest_addoption(parser):
    parser.addoption("--pid", help="PID of LightTools process", type=int)


def open_file(lt, filename):
    # Open the given LightTools file.
    path = os.path.join(os.path.dirname(__file__), "models", filename)
    path = "/".join(path.split("\\"))
    lt.SetOption("SHOWFILEDIALOGBOX", 0)
    lt.Cmd("Open " + lt.Str(path))
    lt.SetOption("SHOWFILEDIALOGBOX", 1)
    lt.Cmd("\V3D")


def teardown(interactive, lt, request):
    # Close LightTools if testing is not interactive.
    def fin():
        if not interactive:
            lt.Cmd("Exit")
    request.addfinalizer(fin)
