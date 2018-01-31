import lighttools.session
import lighttools.config

import pytest


def test_start_new_session():
    ses = lighttools.session.Session.new()
    lt = ses.ltapi
    version = lt.Version(0)
    lt.Cmd("Exit")
    assert version == lighttools.config.VERSION

    with pytest.raises(ValueError):
        ses = lighttools.session.Session.new(version="99.9.9")
