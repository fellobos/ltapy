import os
import subprocess

import lighttools.config
import lighttools.error
import lighttools.session

import pytest


def test_connect_to_running_session():
    with pytest.raises(ValueError):
        lighttools.session.Session(pid=-1)

    with pytest.raises(lighttools.error.TimeOutError):
        lighttools.session.Session(timeout=-1)

    home_dir = lighttools.session._get_home_dir(lighttools.config.VERSION)
    proc = subprocess.Popen(os.path.join(home_dir, "lt.exe"))
    ses = lighttools.session.Session(pid=proc.pid)
    lt = ses.lt
    assert lt.GetServerID() == proc.pid
    proc.kill()


def test_start_new_session():
    with pytest.raises(ValueError):
        ses = lighttools.session.Session.new(version="99.9.9")

    ses = lighttools.session.Session.new()
    lt = ses.lt
    version = lt.Version(0)
    lt.Cmd("Exit")
    assert version == lighttools.config.VERSION
