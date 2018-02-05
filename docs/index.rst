=================================
Welcome to ltapy's documentation!
=================================

This site covers ltapy's usage and API documentation.

ltapy is a Python interface to the API of the `LightTools
<https://www.synopsys.com/optical-solutions/lighttools.html>`_
illumination design software. It provides an **enhanced interface** to
the LightTools API, as well as **extended functionality** to simplify
the programmatic access to LightTools.

Creating a :ref:`connection <connection-capabilities>` and interacting
with LightTools is simple:

.. code-block:: python

    >>> import ltapy.session
    >>> ses = ltapy.session.Session(pid=4711)
    >>> lt = ses.lt
    >>> lt.Message("Successfully connected to LightTools!")

The above connects Python with a running LightTools session
(identified by the given PID) and displays the message in the
LightTools console window.

Usage documentation
-------------------

The following list contains all major sections of ltapy's non-API
documentation.

.. toctree::
    :maxdepth: 2

    usage/install
    usage/enhanced
    usage/extended

API documentation
-----------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
    :maxdepth: 2

    api/core
    api/extension

.. - What is ltapy?
.. - How to use it?
.. - Core functionality (Connection, Error Handling, Database Access)
.. - Extensions (Apodization, Volume Scatter Logger, ...)
.. - API Reference
.. - Installation
.. - License Info

.. - JumpStart library
.. - API documentation



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
