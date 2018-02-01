"""
Utility methods for client-side COM support.

COM client support is the ability to manipulate COM server objects via
their exposed interface. Automation objects (e.g. LightTools) are COM
server objects that expose their methods and properties using the
IDispatch interface. This interface enables them to be accessed by
automation clients, such as Visual Basic or Python.

All COM server objects that are currently running on the computer are
registered in the running object table (ROT). The ROT is a globally
accessible look-up table that keeps track of those objects. The
LightTools API also uses the Microsoft Windows COM interface and
registers its objects with the ROT.

The `RunningObjectTable` class provides easy access to the ROT and to
the COM objects that are registered there. Furthermore, this module
defines a few helper functions in order to support early-bound
automation for IDispatch based COM objects.
"""

import os

import pythoncom
import win32com.client


class RunningObjectTable(object):

    """
    Provide access to COM objects that are registered in the running
    object table (ROT).

    Examples:
        Show the contents of the running object table:

        >>> rot = RunningObjectTable()
        >>> rot.show()
        LightTools API Server | 1912
        LightTools API Server | 6940
        !{0006F03A-0000-0000-C000-000000000046}
        !factory.pulse.juniper.net

        Get the COM object that is identified by a moniker with the
        display name 'LightTools API Server | 6940':

        >>> comobj = rot.get_object(name="LightTools API Server | 6940")
        >>> comobj
        <PyIUnknown at 0x000000000389AD00 with obj at 0x000000000051C1D0>
    """

    def __init__(self):
        self.rot = pythoncom.GetRunningObjectTable()

    def __repr__(self):
        """
        Return the contents of the Running Object Table.

        Returns:
            str: The moniker names of all objects currently found in the
                Running Object Table.
        """
        moniker_names = []
        for moniker in self.rot:
            moniker_names.append(self._get_moniker_name(moniker))
        return "\n".join(moniker_names)

    def _get_moniker_name(self, moniker):
        """
        Return the display name of the given moniker.

        Args:
            moniker (PyIMoniker): The moniker identifying the COM object.

        Returns:
            str: The display name of the moniker.
        """
        return moniker.GetDisplayName(pythoncom.CreateBindCtx(0), None)

    def get_object(self, name):
        """
        Return a COM object from the running object table.

        Args:
            name (str): The display name of the moniker that identifies
                the requested COM object.

        Returns:
            PyIUnknown: The requested COM object.

        Raises:
            ValueError: If a COM object with the given moniker name could not
                be found.
        """
        for moniker in self.rot:
            moniker_name = self._get_moniker_name(moniker)
            if name == moniker_name:
                return self.rot.GetObject(moniker)
        else:
            msg = "Couldn't find COM object with moniker name {!r}."
            raise ValueError(msg.format(name))

    def get_objects(self):
        """
        Return all COM objects from the running object table.

        Args:
            None

        Returns:
            dict: A mapping that contains all running COM objects as
                'moniker_name': <COM object> pairs.
        """
        objs = {}
        for moniker in self.rot:
            moniker_name = self._get_moniker_name(moniker)
            # A race condition might occur if a COM application is closed
            # while the Running Object Table is scanned. There is therefore
            # a chance that the object identified by moniker is not alive
            # any more.
            try:
                obj = self.rot.GetObject(moniker)
            except pythoncom.com_error:
                continue
            else:
                objs[moniker_name] = obj
        return objs


def is_dynamic_dispatch(idispatch):
    """
    Check if a dynamic dispatch object is generated from the given
    interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.

    Returns:
        bool: True if a dynamic dispatch object is generated from the
            given interface.
    """
    disp = win32com.client.Dispatch(idispatch)
    return isinstance(disp, win32com.client.CDispatch)


def generate_typelib_support(idispatch):
    """
    Generate type library support (Python source code) for the IDispatch
    based COM object.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.
    """
    typelib = get_typelib(idispatch)
    win32com.client.gencache.MakeModuleForTypelibInterface(typelib)


def get_typelib(idispatch):
    """
    Return the type library for the given IDispatch interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.

    Returns:
        PyITypeLib: The type library for the given IDispatch object.
    """
    info = idispatch.GetTypeInfo()
    typelib, index = info.GetContainingTypeLib()
    return typelib


def get_generated_filepath(idispatch):
    """
    Return the path of the Python support file which is generated for the
    type library of the given IDispatch interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.

    Returns:
        filepath (str): Absolute filepath of the Python support file.
    """
    typelib = get_typelib(idispatch)
    clsid, lcid, _, major, minor, _ = typelib.GetLibAttr()
    path = win32com.client.gencache.GetGeneratePath()
    filename = win32com.client.gencache.GetGeneratedFileName(
        clsid, lcid, major, minor
    )
    return os.path.join(path, filename + ".py")
