import os

import pytest

import lighttools.session
import lighttools.vslogger


@pytest.fixture(scope="class")
def vslogger(request):
    ltapi, interactive = setup(request)

    # TODO: Extract filename from test module.
    open_file(ltapi, "vslogger.lts")
    key = (
        "lens_manager[1].components[components].solid[phosphor]"
        ".volume_interface[volumeinterface_eos]"
        ".volume_scatter_log[volumescatterlog]"
    )
    vslog = lighttools.vslogger.VolumeScatterLogger(ltapi, key)

    teardown(ltapi, interactive, request)

    return vslog


def setup(request):
    # For interactive testing the LightTools PID can be passed
    # via the command line, e.g. py.test --pid=1234.
    pid = request.config.getoption("--pid")
    interactive = True if pid else False

    # Connect to a running LightTools session or create a new one.
    if interactive:
        ses = lighttools.session.Session(pid)
    else:
        ses = lighttools.session.Session.new()

    return ses.ltapi, interactive


def pytest_addoption(parser):
    # Add a command line option for specifying the LightTools process ID.
    parser.addoption("--pid", help="PID of LightTools process", type=int)


def open_file(ltapi, filename):
    # Open the given LightTools file.
    path = os.path.join(os.path.dirname(__file__), "models", filename)
    path = "/".join(path.split("\\"))
    ltapi.SetOption("SHOWFILEDIALOGBOX", 0)
    ltapi.Cmd("Open " + ltapi.Str(path))
    ltapi.SetOption("SHOWFILEDIALOGBOX", 1)
    ltapi.Cmd("\V3D")


def teardown(ltapi, interactive, request):
    # Close LightTools if testing is not interactive.
    def fin():
        if not interactive:
            ltapi.Cmd("Exit")
    request.addfinalizer(fin)


@pytest.fixture(scope="module")
def lt(request):
    ltapi, interactive = setup(request)
    open_file(ltapi, getattr(request.module, "FILENAME"))
    teardown(ltapi, interactive, request)
    return ltapi
