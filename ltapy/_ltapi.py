"""
This module provides a LightTools API object with enhanced features.
"""

import functools
import inspect
import logging
import os
import string
import tempfile

import numpy as np
import pythoncom
import win32com.client
from win32com.client import constants as LTReturnCodeEnum

from . import _comutils
from . import _dbaccess
from . import error

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# LightTools API functions that return no status code, just a single
# output value.  Also include GetStat() because the purpose of the
# function is to return the status of the most recently executed
# Lighttools command.  Don't error check this return value!
NO_STATUS_CODE_FUNCS = (
    "Coord2",
    "Coord3",
    "GetServerID",
    "GetStat",
    "Str",
    "WasInterrupted",
)

# LightTools API functions where the return values come in swapped
# order.
SWAPPED_ORDER_FUNCS = (
    "DbKeyDump",
    "GetFreeformSurfacePoints",
    "GetReceiverRayData",
    "GetSplineData",
    "GetSplineVec",
    "GetSweptProfilePoints",
    "QuickRayAim",
    "QuickRayQuery",
    "SetMeshData",
    "SetMeshStrings",
    "ViewKeyDump",
)

# LightTools API functions with (partly) redundant output value(s).
REDUNDANT_OUTPUT_FUNCS = (
    "GetMeshData",
    "GetMeshStrings",
    "SetMeshData",
    "SetMeshStrings",
)

# LightTools API functions with an array-like output value.
ARRAY_OUTPUT_FUNCS = (
    "GetFreeformSurfacePoints",
    "GetMeshData",
    "GetMeshStrings",
    "GetReceiverRayData",
    "GetSplineData",
    "GetSplineVec",
    "GetSweptProfilePoints",
)


def LTAPI(comobj, rebuild=False):
    """
    Create an enhanced LightTools COM client object.

    Args:
        comobj (PyIUnknown): The LightTools COM server object.
        rebuild (bool): Wether to regenerate the Python source code
            (MakePy support) for the corresponding COM type library.

    Returns:
        lt (ILTAPIx): A handle to the LightTools session.
    """
    # Get the IDispatch interface of the COM server object.
    idispatch = comobj.QueryInterface(pythoncom.IID_IDispatch)

    # Make sure that MakePy support is available for the object.
    _ensure_makepy_support(idispatch, rebuild)

    # Create an early-bound LightTools COM client object.
    lt = win32com.client.Dispatch(idispatch)

    # Enhance the default LightTools API with additional features.
    _enable_exceptions(lt)
    _improve_dblist_interface(lt)
    _fix_dbkeydump_argspec(lt)
    _fix_viewkeydump_argspec(lt)

    return lt


def _ensure_makepy_support(idispatch, rebuild=False):
    """
    Ensure that MakePy support exists for the IDispatch based COM object.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of a LightTools
            COM server object.
        rebuild (bool): Wether to regenerate the Python source code
            (makepy support) for the corresponding COM type library.
    """
    if rebuild or _comutils.is_dynamic_dispatch(idispatch):
        _comutils.generate_typelib_support(idispatch)


def _enable_exceptions(lt):
    """
    Enable exceptions for the given LightTools COM object.

    Force LightTools to raise an exception if an API function call returns
    with a non-zero error code.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
    """
    if _has_exceptions(lt):
        return
    for name, method in inspect.getmembers(lt, inspect.ismethod):
        if not _is_api_method(method):
            continue
        setattr(lt.__class__, name, _catch_return_value(method.__func__))


def _has_exceptions(lt):
    """
    Check if the given LightTools COM object can raise exceptions.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.

    Returns:
        bool: True if exceptions are enabled for the LightTools COM
            object.
    """
    # If exceptions are not enabled the DbGet() function returns a tuple,
    # e.g. ('C:\\Users\\...\\...\\LightToolsLogs\\LightTools.194.log', 0).
    result = lt.DbGet("LENS_MANAGER[1]", "LogFileName")
    if isinstance(result, tuple):
        return False
    else:
        return True


def _is_api_method(method):
    """
    Check wether the given method is a LightTools API method.

    The names of all LightTools API methods start with an uppercase ASCII
    character.  Therefore, the first letter of the method name is checked
    (must be ASCII uppercase) in order to determine if the given method is
    a LightTools API method or not.

    Args:
        method (method): A bound method of an ILTAPIx class instance.

    Returns:
        bool: True if the given `method` is a LightTools API method.
    """
    name = method.__name__
    first_letter = name[0]
    return first_letter in string.ascii_uppercase


def _catch_return_value(func):
    """
    Catch the return value of a LightTools API function call.

    Intercept the return value of a LightTools API function call
    and forward it to an error checking function that raises an exception
    if the returned error code has a non-zero value.

    Args:
        func (function): The function object of a (bound) LightTools
            API method.

    Returns:
        function: The wrapped function object.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return_value = func(*args, **kwargs)
        lt, *args = args
        func_name = func.__name__
        msg = "Calling LTAPI function {}, args={}, kwargs={}, retval={}"
        log.debug(msg.format(repr(func_name), args, kwargs, return_value))
        return _process_return_value(lt, func_name, return_value)
    return wrapper


def _process_return_value(lt, func_name, return_value):
    """
    Process the return value(s) of a Lighttools API function call.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
        func_name (str): The name of the LightTools API function.
        return_value (scalar or tuple): Return value(s) of the unprocessed
            LightTools API function call.

    Returns:
        The processed output value of the LightTools API function.

    Raises:
        APIError: If the LightTools API function call returns with a
            non-zero status code.
    """
    status = None
    out = None
    unexpected = False

    if func_name in NO_STATUS_CODE_FUNCS:
        status = None
        out = return_value
    elif isinstance(return_value, int):
        status = return_value
        out = None
    elif isinstance(return_value, tuple):
        if len(return_value) == 2:
            if func_name in SWAPPED_ORDER_FUNCS:
                status, out = return_value
            else:
                out, status = return_value
            if func_name in REDUNDANT_OUTPUT_FUNCS:
                out = None
        elif len(return_value) == 3:
            if func_name in SWAPPED_ORDER_FUNCS:
                *out, status = return_value
            else:
                status, *out = return_value
            if func_name in REDUNDANT_OUTPUT_FUNCS:
                out = out[0]
        else:
            unexpected = True
    else:
        unexpected = True

    if unexpected:
        msg = "Unexpected return value from LTAPI function {}: {}"
        raise ValueError(msg.format(repr(func_name), return_value))

    if func_name in ARRAY_OUTPUT_FUNCS:
        out = np.array(out)

    msg = "Processing return value of LTAPI function {}, status={}, out={}"
    log.debug(msg.format(repr(func_name), status, out))

    if status and status != LTReturnCodeEnum.ltStatusSuccessInternal:
        raise error.APIError(lt, status)

    return out


def _improve_dblist_interface(lt):
    """
    Improve the database list interface of the given LightTools COM object.

    Replace the default DbList() API method with a function that returns
    an enhanced DbList object.  The original DbList() API method can still
    be accessed from the object by using an underscore prefix (lt._DbList).

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
    """
    # This function must be executed only once, in order to avoid that the
    # original lt._DbList() function gets overwritten.
    if hasattr(lt, "_DbList"):
        return

    # A hard to detect error happened during tests when switching bewteen
    # two LightTools processes during one Python session:
    # - The first error was, that 'lt' (instead of self) was handed to the
    #   DbList wrapper function.
    # - The second error was, that the class method, instead of the
    #   corresponding function object, was hidden under the underscore
    #   prefixed name.

    doc = lt.DbList.__func__.__doc__
    setattr(lt.__class__, "_DbList", lt.DbList.__func__)# must be __func__

    def DbList(self, dataKey=pythoncom.Empty, filter=pythoncom.Empty, status=0):
        return _dbaccess.DbList(self, dataKey, filter)

    DbList.__doc__ = doc
    setattr(lt.__class__, "DbList", DbList)


def _fix_dbkeydump_argspec(lt):
    """
    Fix a bug in the argspec of the DbKeyDump API method.

    The optional parameter fileName has a wrong default value of '0'.
    If fileName is not specified, the list of data values is written
    to a file with name '0', instead of being printed to the LightTools
    console window.

    Replace the original DbKeyDump() API method with a wrapper function
    that provides a correct default value for the fileName parameter.
    The original DbKeyDump() API method can still be accessed by using an
    underscore prefix (lt._DbKeyDump).

    As additional feature, printed output also goes to the Python console
    window.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
    """
    # This function must be executed only once, to avoid that the original
    # lt._DbKeyDump() function gets overwritten.
    if hasattr(lt, "_DbKeyDump"):
        return

    doc = lt.DbKeyDump.__func__.__doc__
    setattr(lt.__class__, "_DbKeyDump", lt.DbKeyDump.__func__)

    def DbKeyDump(self, dataKey=pythoncom.Empty, fileName=pythoncom.Empty):
        print_to_console = (fileName == pythoncom.Empty)
        if print_to_console:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
                self._DbKeyDump(dataKey, f.name)
                f.seek(0)
                print(f.read())
            os.remove(f.name)
            fileName = ""
        return self._DbKeyDump(dataKey, fileName)

    DbKeyDump.__doc__ = doc
    setattr(lt.__class__, "DbKeyDump", DbKeyDump)


def _fix_viewkeydump_argspec(lt):
    """
    Fix a bug in the argspec of the ViewKeyDump API method.

    The optional parameter fileName has a wrong default value of '0'.
    If fileName is not specified, the list of data values is written
    to a file with name '0', instead of being printed to the LightTools
    console window.

    Replace the original ViewKeyDump() API method with a wrapper function
    that provides a correct default value for the fileName parameter.
    The original ViewKeyDump() API method and can still be accessed by
    using an underscore prefix (lt._ViewKeyDump).

    As additional feature, printed output also goes to the Python console
    window.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
    """
    # This function must be executed only once, to avoid that the original
    # lt._ViewKeyDump() function gets overwritten.
    if hasattr(lt, "_ViewKeyDump"):
        return

    doc = lt.ViewKeyDump.__func__.__doc__
    setattr(lt.__class__, "_ViewKeyDump", lt.ViewKeyDump.__func__)

    def ViewKeyDump(self, viewKey=pythoncom.Empty, fileName=pythoncom.Empty):
        print_to_console = (fileName == pythoncom.Empty)
        if print_to_console:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
                self._ViewKeyDump(viewKey, f.name)
                f.seek(0)
                print(f.read())
            os.remove(f.name)
            fileName = ""
        return self._ViewKeyDump(viewKey, fileName)

    ViewKeyDump.__doc__ = doc
    setattr(lt.__class__, "ViewKeyDump", ViewKeyDump)
