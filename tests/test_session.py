import os
import subprocess

import ltapy.config
import ltapy.error
import ltapy.session

import pytest


def test_connect_to_running_session():
    with pytest.raises(ValueError):
        ltapy.session.Session(pid=-1)

    with pytest.raises(ltapy.error.TimeOutError):
        ltapy.session.Session(timeout=-1)

    home_dir = ltapy.session._get_home_dir(ltapy.config.LT_VERSION)
    proc = subprocess.Popen(os.path.join(home_dir, "lt.exe"))
    ses = ltapy.session.Session(pid=proc.pid)
    lt = ses.lt
    assert lt.GetServerID() == proc.pid
    proc.kill()


def test_start_new_session():
    with pytest.raises(ValueError):
        ses = ltapy.session.Session.new(version="99.9.9")

    ses = ltapy.session.Session.new()
    lt = ses.lt
    version = lt.Version(0)
    lt.Cmd("Exit")
    assert version == ltapy.config.LT_VERSION
