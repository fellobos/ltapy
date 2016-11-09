"""
A COM client object for the JumpStart macro function library.
"""

import functools
import inspect

import pythoncom
import win32com.client

from . import comutils


def JSLIB(progid, rebuild=False):
    """
    Create a COM client object for the JumpStart macro function library
    that uses early-bound automation.

    Args:
        progid (str): The ProgID for the JumpStart COM object.
        rebuild (bool): Wether to regenerate the Python source code
            (MakePy support) for the corresponding COM type library.

    Returns:
        jslib (JSNET): A handle to the JumpStart macro function library.
    """
    # Make sure that MakePy support is available for the object.
    ensure_makepy_support(progid, rebuild)

    # Create an early-bound JumpStart COM client object.
    jslib = win32com.client.Dispatch(progid)

    return jslib


def ensure_makepy_support(progid, rebuild=False):
    """
    Ensure that MakePy support exists for the COM object identified by the
    given ProgID.

    Args:
        progid (str): The ProgID for the JumpStart COM object.
        rebuild (bool): Wether to regenerate the Python source code
            (MakePy support) for the corresponding COM type library.
    """
    try:
        # Get the JumpStart library object that is associated with the given
        # ProgID. If MakePy support is already available an early-bound
        # (static dispatch) COM object will be generated, a late-bound
        # (dynamic dispatch) COM object otherwise. NOTE: No support files are
        # generated at this step!
        jslib = win32com.client.Dispatch(progid)
    except NameError:
        # This exception is raised if support files are available but
        # incorrect ("name 'nan' is not defined" error due to a bug in
        # MakePy). Rebuilding of the support files is necessary! The IDispatch
        # interface (needed for rebuilding) is queried from a late-bound
        # (dynamic dispatch) JumpStart library object. This makes sure that
        # the incorrect support files are not used for object creation.
        rebuild = True
        jslib = win32com.client.dynamic.Dispatch(progid)
        idispatch = jslib._oleobj_.QueryInterface(pythoncom.IID_IDispatch)
    else:
        # Update the IDispatch interface because the generated JumpStart
        # library object might already be an early-bound COM automation
        # object. Generation of MakePy support is not necessary in this case.
        idispatch = jslib._oleobj_.QueryInterface(pythoncom.IID_IDispatch)

    # Only generate the support files and load the module if explicitly
    # required (rebuild=True) or if the JumpStart library object is a
    # late-bound (dynamic dispatch) COM object.
    if rebuild or comutils.is_dynamic_dispatch(idispatch):
        try:
            comutils.generate_typelib_support(idispatch)
        except NameError:
            # Fix "name 'nan' is not defined" NameError exception and add the
            # module to the cache.
            srcfile = comutils.get_generated_filepath(idispatch)
            with open(srcfile, "r+") as f:
                data = f.read()
                f.seek(0)
                f.write(data.replace("=nan", "=defaultNamedNotOptArg"))
            typelib = comutils.get_typelib(idispatch)
            clsid, lcid, _, major, minor, _ = typelib.GetLibAttr()
            win32com.client.gencache.AddModuleToCache(
                clsid, lcid, major, minor
            )
