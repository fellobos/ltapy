"""
Manage the connection to a LightTools session.
"""

import os
import subprocess
import time
import winreg

import psutil

from . import _comutils
from . import config
from . import error
from . import _ltapi


def _get_lt_home(version):
    """
    Return the LightTools home directory.

    Get the home directory of the specified LightTools `version` from the
    Windows registry. The requested LightTools `version` must be installed
    on the system.

    Args:
        version (str): The LightTools version string, e.g. "8.5.0".

    Returns:
        str: The LightTools home directory.
    """
    try:
        hkey = winreg.OpenKeyEx(
            key=winreg.HKEY_LOCAL_MACHINE,
            sub_key="SOFTWARE\\Optical Research Associates\\LightTools\\{}\\Environment".format(
                version
            ),
        )
    except OSError:
        msg = (
            "Couldn't find home directory of LighTools version {!r}. Please "
            "check if the requested LightTools version is installed."
        )
        raise ValueError(msg.format(version))
    else:
        value, __ = winreg.QueryValueEx(hkey, "LT_HOME")
        return value


class Session(object):

    """
    Create a connection to a LightTools session.

    The connection to LightTools can be established in the following ways:

    * Connect to an already running LightTools session by specifying the
      PID of the LightTools process.

    * Start a new LightTools session and connect to that session by
      specifying the display name of the desired LightTools version (see
      Session.new() for further details).

    The generated LighTools API object (ltapi) has advanced error handling
    capabilities. Instead of just returning the error code (the default
    behaviour), the enhanced LightTools API object checks the return value
    of an API function call and raises an APIError exception if the
    function returns with an error.

    Args:
        pid (int, optional): The process ID of an already running
            LightTools session. If pid is given connect to that specific
            session, otherwise connect to an arbitrary, running LightTools
            session.
        timeout (int, optional): The time limit in seconds after which a
            connection attempt to LightTools is aborted.

    Attributes:
        ltapi (ILTAPIx): A handle to the LightTools session.
        pid (int): The PID of the LightTools process.

    Raises:
        TimeOutError: If a connection attempt with LightTools was aborted
            due to timeout.

    Examples:
        Connect to a running LightTools session by specifying the PID of
        the LightTools process.

        >>> ses = lts.Session(pid=5642)
        >>> lt = ses.ltapi
        >>> lt.Message("Connected to LightTools, PID: {}".format(ses.pid))

        Start a new LightTools session (by specifiying the display name of
        the desired version) and connect to that session.

        >>> lts.installed_versions()
        ['LightTools(64) 8.3.2', 'LightTools(64) 8.4.0']
        >>> ses = lts.Session.new(version="LightTools(64) 8.4.0")
        >>> lt = ses.ltapi
    """

    def __init__(self, pid=None, timeout=config.TIMEOUT, _rebuild=False):
        self.pid = pid
        self._timeout = timeout
        self._rebuild = _rebuild

        # Get a handle to the LightTools session.
        comobj = self._get_COM_object()
        self.ltapi = _ltapi.LTAPI(comobj, self._rebuild)

        # Set the process ID if the connection was established with an
        # arbitrary LightTools session.
        if not self.pid:
            self.pid = self.ltapi.GetServerID()

    def _get_COM_object(self):
        """
        Return a LightTools COM server object from the running object table.

        Returns:
            comobj (PyIUnknown): The LightTools COM server object. If no
                process ID was given return an arbitrary LightTools COM object
                from the running object table.
        """
        prefix = "LightTools API Server | "

        if self.pid:
            if not psutil.pid_exists(self.pid):
                msg = "Couldn't find LightTools process with PID: {}"
                raise ValueError(msg.format(self.pid))
            prefix += str(self.pid)

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
            msg = ("Connection attempt with LightTools aborted due to "
                   "timeout: {} sec")
            raise error.TimeOutError(msg.format(self._timeout))

    @classmethod
    def new(cls, version=config.VERSION, timeout=config.TIMEOUT, _rebuild=False):
        """
        Start a new instance of LightTools and connect to that session.

        Args:
            version (str, optional): The LightTools version to be started.
            timeout (int, optional): Time limit in seconds after which the
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
        >>> lt = ses.ltapi
        """
        lt_home = _get_lt_home(version)
        proc = subprocess.Popen(os.path.join(lt_home, "lt.exe"))
        return cls(proc.pid, timeout, _rebuild)
