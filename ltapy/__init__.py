"""
ltapy

ltapy is a Python interface to the API of the `LightTools`_
illumination design software.  It provides an enhanced interface to
the LightTools API, as well as extended functionality to simplify the
programmatic access to LightTools.

Examples:
    Creating a connection and interacting with LightTools is simple:

    >>> import ltapy.session
    >>> ses = ltapy.session.Session(pid=5612)
    >>> lt = ses.lt
    >>> lt.Message("Connected to LightTools")

    The above connects Python with a running LightTools session
    (identified by the given PID) and displays the message in the
    LightTools console window.

Notes:
    Documentation is available as docstrings provided with the code
    or online as usage and reference documentation at
    `fellobos.github.io`_.

.. _LightTools:
   https://www.synopsys.com/optical-solutions/lighttools.html

.. _fellobos.github.io:
   https://fellobos.github.io/ltapy
"""

__version__ = "0.2.1"
