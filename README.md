# ltapy

ltapy is a Python interface to the API of the [LightTools][1]
illumination design software. It provides an **enhanced interface** to
the LightTools API, as well as **extended functionality** to simplify
the programmatic access to LightTools.

Creating a connection and interacting with LightTools is simple:

    >>> import ltapy.session
    >>> ses = ltapy.session.Session(pid=4711)
    >>> lt = ses.lt
    >>> lt.Message("Successfully connected to LightTools!")

The above connects Python with a running LightTools session
(identified by the given PID) and displays the message in the
LightTools console window.

## Installation

Clone the public repository to get a local copy of the source:

    $ git clone git://github.com/fellobos/ltapy.git

Once you have it, you can embed ltapy in your own Python package, or
install it into your site-packages easily:

    $ cd ltapy
    $ python setup.py install

## Documentation

ltapy has usage and reference documentation available at
[fellobos.github.io][2].

[1]: https://www.synopsys.com/optical-solutions/lighttools.html
[2]: https://fellobos.github.io/ltapy
