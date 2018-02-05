"""
This module contains the LightTools exception classes.
"""


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
        status (int): Status code of the LightTools API function call.
    """

    def __init__(self, ltapi, status):
        self.ltapi = ltapi
        self.status = status

    def __str__(self):
        return "[{status}] {message}".format(
            status=str(self.status),
            message=self.ltapi.GetStatusString(self.status),
        )
