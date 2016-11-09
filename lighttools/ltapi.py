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
import string

import pythoncom
import win32com.client

from . import comutils
from . import dbaccess
from . import error


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
        result = func(*args, **kwargs)
        ltapi = args[0]
        return error.raise_exception_on_error(ltapi, func.__name__, result)
    return wrapper


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

    doc = ltapi.DbList.__func__.__doc__
    setattr(ltapi.__class__, "_DbList", ltapi.DbList)

    def DbList(self, key=pythoncom.Empty, filter=pythoncom.Empty, status=0):
        """
        Return an enhanced DbList object.

        This ia a wrapper function that returns an enhanced DbList object and
        mimics the call syntax (ArgSpec) of the original DbList function.
        """
        return dbaccess.DbList(self, key, filter)

    DbList.__doc__ = doc
    setattr(ltapi.__class__, "DbList", DbList)
