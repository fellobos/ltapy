"""
This module provides connection capabilities to LightTools.
"""

import os
import subprocess
import time
import winreg

import psutil

from . import _comutils
from . import _ltapi
from . import config
from . import error


def _get_home_dir(version):
    """
    Return the LightTools home directory.

    Get the home directory of the specified LightTools `version` from the
    Windows registry.  The requested LightTools `version` must be installed
    on the system.

    Args:
        version (str): The LightTools `version` string, e.g. "8.5.0".

    Returns:
        str: The LightTools home directory.
    """
    try:
        hkey = winreg.OpenKeyEx(
            key=winreg.HKEY_LOCAL_MACHINE,
            sub_key=(
                "SOFTWARE\\Optical Research Associates\\LightTools"
                "\\{}\\Environment"
            ).format(version),
        )
    except OSError:
        msg = (
            "Couldn't find home directory of LighTools version {!r}. Please "
            "check if the requested version of LightTools is installed."
        )
        raise ValueError(msg.format(version))
    else:
        value, __ = winreg.QueryValueEx(hkey, "LT_HOME")
        return value


class Session:

    """
    Connect to a running LightTools session.

    Create a connection to a running LightTools session, using Python as
    client program.  The `lt` attribute provides a handle to the
    connected session.

    Args:
        pid (int, optional): The process ID of an already running
            LightTools session.  If `pid` is given connect to that specific
            session, otherwise connect to an arbitrary session.
        timeout (int, optional): The time limit in seconds after which a
            connection attempt to LightTools is aborted.

    Attributes:
        lt (ILTAPIx): A handle to the LightTools session.

    Raises:
        TimeOutError: If a connection attempt with LightTools was aborted
            due to timeout.

    Examples:
        Connect to a running LightTools session by specifying the PID of
        the LightTools process.

        >>> ses = Session(pid=5642)
        >>> lt = ses.lt
        >>> lt.Message("Successfully connected to LightTools!")
    """

    def __init__(self, pid=None, timeout=config.TIMEOUT, _rebuild=False):
        self._pid = pid
        self._timeout = timeout
        self._rebuild = _rebuild

        # Get a handle to the LightTools session.
        comobj = self._get_COM_object()
        self.lt = _ltapi.LTAPI(comobj, self._rebuild)

        # Get the process ID if connected to an arbitrary LightTools session.
        if not self._pid:
            self._pid = self.lt.GetServerID()

    def _get_COM_object(self):
        """
        Return a LightTools COM server object from the Running Object Table.

        Returns:
            comobj (PyIUnknown): The LightTools COM server object.  If no
                process ID was given return an arbitrary LightTools COM object
                from the Running Object Table.
        """
        prefix = "LightTools API Server | "

        if self._pid:
            if not psutil.pid_exists(self._pid):
                msg = "Couldn't find a LightTools process with PID {}."
                raise ValueError(msg.format(self._pid))
            prefix += str(self._pid)

        start_time = time.time()
        connection_attempt_timed_out = (
            lambda current_time: current_time - start_time > self._timeout
        )

        rot = _comutils.RunningObjectTable()

        while not connection_attempt_timed_out(time.time()):
            comobjs = rot.get_objects()
            for name in comobjs:
                if name.startswith(prefix):
                    return comobjs[name]
        else:
            msg = (
                "Couldn't establish a connection to LightTools within {} "
                "seconds. Connection attempt aborted."
            )
            raise error.TimeOutError(msg.format(self._timeout))

    @classmethod
    def new(cls, version=config.LT_VERSION, timeout=config.TIMEOUT,
            _rebuild=False):
        """
        Start a new LightTools instance and connect to that session.

        Args:
            version (str, optional): The LightTools version to be started.
            timeout (int, optional): The time limit in seconds after which the
                connection attempt to LightTools is aborted.

        Returns:
            Session: A session object, connected with the newly created
                LightTools instance.

        Raises:
            TimeOutError: If a connection attempt with LightTools was aborted
                due to timeout.

        Examples:
            Start a new LightTools instance and connect to that session:

        >>> ses = Session.new(version="8.5.0")
        >>> lt = ses.lt
        >>> lt.Message("Successfully connected to LightTools!")
        """
        home_dir = _get_home_dir(version)
        proc = subprocess.Popen(os.path.join(home_dir, "lt.exe"))
        return cls(proc.pid, timeout, _rebuild)
