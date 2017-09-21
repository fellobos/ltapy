"""
Error handling for LightTools API functions and custom exceptions.
"""

import numpy as np
import win32com.client

# LightTools API functions w/o error code.
NO_ERROR_CODE_FUNCS = (
    "Coord2", "Coord3", "GetServerID", "Str", "WasInterrupted"
)


def raise_exception_on_error(ltapi, func_name, *args):
    """
    Raise an exception when a LightTools API function returns an error.

    Args:
        ltapi (ILTAPIx): Handle to the LightTools session.
        func_name (str): Name of the LightTools API function.
        *args (tuple): Return value(s) of the LightTools API function.

    Returns:
        The return value of the called LightTools API function.

    Raises:
        APIError: If the LightTools API function returns with a non-zero
            error code.
    """
    # Return values come in as tuple, e.g. ((u'Intensity Mesh', 0),) or (76,).
    return_values, = args
    if func_name in NO_ERROR_CODE_FUNCS:
        # Functions with value, no error code, e.g. GetServerID().
        return_value = return_values
        error_code = None
    elif isinstance(return_values, int):
        # Functions with error code, no value, e.g. Cmd().
        return_value = None
        error_code = int(return_values)
    elif isinstance(return_values, tuple) and len(return_values) == 2:
        # Functions with error code and value, e.g. DbGet().
        return_value, error_code = return_values
        if func_name == "DbKeyDump":  # wrong order of return values
            error_code, return_value = return_value, None
        error_code = int(error_code)
    elif isinstance(return_values, tuple) and len(return_values) == 3:
        # Functions with error code, value and filter, e.g. GetMeshData().
        error_code, return_value, cell_filter = return_values
        error_code = int(error_code)
        return_value = np.array(return_value)
    else:
        msg = "Expected int or tuple of length <= 3: {}"
        raise TypeError(msg.format(return_values))
    if error_code:
        raise APIError(ltapi, error_code)
    return return_value


class LightToolsError(Exception):
    """
    Base class for all LightTools exceptions.
    """


class TimeOutError(LightToolsError):
    """
    Raised when a connection attempt to LightTools was aborted due to
    timeout.
    """


class APIError(LightToolsError):

    """
    Raised when a LightTools API function returns a nonzero error code.

    Args:
        ltapi (ILTAPIx): Handle to the LightTools session.
        error_code (int): Error code of the LightTools API function.
    """

    def __init__(self, ltapi, error_code):
        self.ltapi = ltapi
        self.error_code = error_code
        self.error_meaning = self.get_error_meaning()
        self.error_message = self.get_error_message()

    def __str__(self):
        return "{meaning} ({code}): {message}".format(
            meaning=self.error_meaning,
            code=self.error_code,
            message=self.error_message
        )

    def get_error_meaning(self):
        for d in win32com.client.constants.__dicts__:
            for error_meaning, error_code in d.items():
                if (error_meaning.startswith("ltStatus")
                    and error_code == self.error_code):
                    return error_meaning
        else:
            msg = "Could not get meaning of LightTools error code {!r}."
            raise ValueError(msg.format(self.error_code))

    def get_error_message(self):
        message_type = 1  # 1 means return last error message
        error_message = self.ltapi.GetLastMsg(message_type)
        try:
            head, sep, tail = error_message.partition("Error: ")
        except AttributeError:
            return ""
        else:
            return tail if tail else "No error message available."
