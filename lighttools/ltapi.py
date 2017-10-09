"""
An enhanced LightTools COM client object.

This module provides an enhanced client object that is connected to a
LightTools COM session using early-bound (static dispatch) automation.
The generated LightTools COM object has advanced error handling
capabilities and provides an improved interface for working with
database lists.
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

from . import comutils
# from . import dbaccess
from . import error
import lighttools.dbaccess

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# LightTools API functions that return no status code, just a single output
# value. Also include GetStat() because the purpose of the function is to
# return the status of the most recently executed Lighttools command. Don't
# error check this return value!
NO_STATUS_CODE_FUNCS = (
    "Coord2",
    "Coord3",
    "GetServerID",
    "GetStat",
    "Str",
    "WasInterrupted",
)

# LightTools API functions where the return values come in swapped order.
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
    Create an enhanced LightTools COM client object that uses early-bound
    automation.

    Args:
        comobj (PyIUnknown): The LightTools COM server object.
        rebuild (bool): Wether to regenerate the Python source code
            (MakePy support) for the corresponding COM type library.

    Returns:
        ltapi (ILTAPIx): A handle to the LightTools session.
    """
    # Get the IDispatch interface of the COM server object.
    idispatch = comobj.QueryInterface(pythoncom.IID_IDispatch)

    # Make sure that MakePy support is available for the object.
    ensure_makepy_support(idispatch, rebuild)

    # Create an early-bound LightTools COM client object.
    ltapi = win32com.client.Dispatch(idispatch)

    # Enhance the default LightTools session object (ILTAPIx) with
    # additional features.
    enable_exceptions(ltapi)
    improve_dblist_interface(ltapi)
    fix_dbkeydump_argspec(ltapi)
    fix_viewkeydump_argspec(ltapi)

    return ltapi


def ensure_makepy_support(idispatch, rebuild=False):
    """
    Ensure that MakePy support exists for the IDispatch based COM object.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of a LightTools
            COM server object.
        rebuild (bool): Wether to regenerate the Python source code
            (makepy support) for the corresponding COM type library.
    """
    if rebuild or comutils.is_dynamic_dispatch(idispatch):
        comutils.generate_typelib_support(idispatch)


def enable_exceptions(ltapi):
    """
    Enable exceptions for the given LightTools COM object.

    This forces LightTools to raise an exception if an API function call
    returns with an error; instead of just returning a non-zero error code
    (which is the default behaviour).

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.
    """
    if has_exceptions(ltapi):
        return
    for name, method in inspect.getmembers(ltapi, inspect.ismethod):
        if not is_api_method(method):
            continue
        setattr(ltapi.__class__, name, catch_return_value(method.__func__))


def has_exceptions(ltapi):
    """
    Check if the given LightTools COM object can raise exceptions.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Returns:
        bool: True if exceptions are enabled for the LightTools COM
            object.
    """
    # If exceptions are not enabled the DbGet function returns a tuple,
    # e.g. ('C:\\Users\\...\\...\\LightToolsLogs\\LightTools.194.log', 0).
    result = ltapi.DbGet("LENS_MANAGER[1]", "LogFileName")
    if isinstance(result, tuple):
        return False
    else:
        return True


def is_api_method(method):
    """
    Check wether the given method is a LightTools API method.

    The names of all LightTools API methods start with an uppercase ASCII
    character. Therefore, the first letter of the method name is checked
    (must be ASCII uppercase) in order to determine if the given method is
    a LightTools API method or not.

    Args:
        method (method): A bound method of an ILTAPIx class instance.

    Returns:
        bool: True if the given method is a LightTools API method.
    """
    name = method.__name__
    first_letter = name[0]
    return first_letter in string.ascii_uppercase


def catch_return_value(func):
    """
    Catch the return value of a LightTools API function call and forward
    it to an error checking function that conditionally raises an
    exception.

    Args:
        func (function): The function object of a (bound) LightTools
            API method.

    Returns:
        function: The wrapped function object.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return_value = func(*args, **kwargs)
        ltapi, *args = args
        func_name = func.__name__
        msg = "Calling LTAPI function {}, args={}, kwargs={}, retval={}"
        log.debug(msg.format(repr(func_name), args, kwargs, return_value))
        return process_return_value(ltapi, func_name, return_value)
    return wrapper


def process_return_value(ltapi, func_name, return_value):
    """
    Process the return value(s) from a Lighttools API function call.

    Args:
        ltapi (ILTAPIx): Handle to the LightTools session.
        func_name (str): Name of the LightTools API function.
        return_value (scalar or tuple): Return value(s) of unprocessed
            LightTools API function call.

    Returns:
        The processed output value of the LightTools API function.

    Raises:
        APIError: If the LightTools API function call returns with a nonzero
            status code.
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
        raise error.APIError(ltapi, status)

    return out


def improve_dblist_interface(ltapi):
    """
    Improve the DbList interface of the given LightTools COM object.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Notes:
        The default DbList API method is replaced with a function that
        returns an enhanced DbList object. The original DbList API method
        is not overwritten and can be accessed from the object via an
        underscore prefix (ltapi._DbList).
    """
    # This function must be executed only once, in order to avoid that the
    # original ltapi._DbList() function gets overwritten.
    if hasattr(ltapi, "_DbList"):
        return

    # Hard to detect error happened in pytest when switching bewteen two
    # LightTools processes during one Python session.
    # - First error was that ltapi (instead of self) was handed to the wrapper
    # fucntion.
    # - Second error was that the class method (instead of the corresponding
    # function object) was hidden under the prefixed name.

    doc = ltapi.DbList.__func__.__doc__
    setattr(ltapi.__class__, "_DbList", ltapi.DbList.__func__)

    def DbList(self, dataKey=pythoncom.Empty, filter=pythoncom.Empty, status=0):
        """
        Return an enhanced DbList object.

        This ia a wrapper function that returns an enhanced DbList object and
        mimics the call syntax (ArgSpec) of the original DbList function.
        """
        return lighttools.dbaccess.DbList(self, dataKey, filter)

    DbList.__doc__ = doc
    setattr(ltapi.__class__, "DbList", DbList)


def fix_dbkeydump_argspec(ltapi):
    """
    Fix a bug in the argspec of the DbKeyDump API method.

    The optional parameter fileName has a wrong default value of "0".
    If fileName is not specified, the list of data values is written
    to a file with name "0", instead of being printed to the LightTools
    console window.

    Replace the original DbKeyDump API method with a wrapper function that
    provides a correct default value for the fileName parameter.
    As additional feature, printed output also goes to the Python console
    window.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Notes:
        The original DbKeyDump API method is not overwritten and can be
        accessed via single underscore prefix (ltapi._DbKeyDump).
    """
    # This function must be executed only once, to avoid that the original
    # ltapi._DbKeyDump() function gets overwritten.
    if hasattr(ltapi, "_DbKeyDump"):
        return

    doc = ltapi.DbKeyDump.__func__.__doc__
    setattr(ltapi.__class__, "_DbKeyDump", ltapi.DbKeyDump.__func__)  # must be __func__

    def DbKeyDump(self, dataKey=pythoncom.Empty, fileName=pythoncom.Empty):
        """
        Call the original DbKeyDump API method with correct parameter
        values and print data values also to the Python console window.
        """
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
    setattr(ltapi.__class__, "DbKeyDump", DbKeyDump)


def fix_viewkeydump_argspec(ltapi):
    """
    Fix a bug in the argspec of the DbKeyDump API method.

    The optional parameter fileName has a wrong default value of "0".
    If fileName is not specified, the list of data values is written
    to a file with name "0", instead of being printed to the LightTools
    console window.

    Replace the original DbKeyDump API method with a wrapper function that
    provides a correct default value for the fileName parameter.
    As additional feature, printed output also goes to the Python console
    window.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Notes:
        The original DbKeyDump API method is not overwritten and can be
        accessed via single underscore prefix (ltapi._DbKeyDump).
    """
    # This function must be executed only once, to avoid that the original
    # ltapi._DbKeyDump() function gets overwritten.
    if hasattr(ltapi, "_ViewKeyDump"):
        return

    doc = ltapi.ViewKeyDump.__func__.__doc__
    setattr(ltapi.__class__, "_ViewKeyDump", ltapi.ViewKeyDump.__func__)

    def ViewKeyDump(self, viewKey=pythoncom.Empty, fileName=pythoncom.Empty):
        """
        Call the original ViewKeyDump API method with correct parameter
        values and print data values also to the Python console window.
        """
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
    setattr(ltapi.__class__, "ViewKeyDump", ViewKeyDump)
