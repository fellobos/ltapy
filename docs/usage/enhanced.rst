==========================
The enhanced API interface
==========================

This page gives a good introduction in how to get started with the
core functionality that is provided by ltapy.

Before you begin, make sure that ltapy is :doc:`installed <install>`
properly on your system.

To use the Python interface to the LightTools API you first have to
create a :ref:`connection <connection-capabilities>` to LightTools.

.. _connection-capabilities:

Connection capabilities
-----------------------

Connecting to a LightTools session is simple. The :class:`Session
<ltapy.session.Session>` object enables you to connect either to a
running LightTools session or to start a new instance of LightTools
and connect to that session:

.. code-block:: python

    >>> import ltapy.session
    >>> ses = ltapy.session.Session(pid=4711)
    >>> lt = ses.lt

The above, connects Python with a running LightTools session that has
the given process ID (PID). If no PID is given, a connection to an
arbitrary LightTools session will be established.

You can start a new instance of LightTools and connect to that session
by specifying the version string of the desired LightTools version.
This requires, of course, that the wanted version of LightTools is
installed on your system:

.. code-block:: python

    >>> import ltapy.session
    >>> ses = ltapy.session.Session.new(version="8.5.0")
    >>> lt = ses.lt

In either case you have now an enhanced LightTools API object called
``lt``:

.. code-block:: python

    >>> lt
    <win32com.gen_py.LightTools 4.0 Type Library.ILTAPI4 instance at 0x137756456>


In addition to the standard LightTools API functions, the enhanced
LightTools API object provides :ref:`automatic error handling
<automatic-error-handling>` and an :ref:`advanced DbList() interface
<advanced-dblist-interface>`.

.. _automatic-error-handling:

Automatic error handling
------------------------

Most LightTools API functions return a status code to indicate wether
the LightTools command completed successfully or not. If the command
was executed without error, the returned value is zero, or otherwise,
greater than zero if an error occured.

The following code example could be from an appliation such as Visual
Basic (VB), using the standard LightTools API. The database access in
the highlighted line results in an error (indicated by the non-zero
status code) because there is a typo in the given data access key:

.. code-block:: none
    :emphasize-lines: 4

    >>> logfile = lt.DbGet("LENS_MANAGER[1]", "LogFileName", status)
    >>> Debug.Print(status)
    0
    >>> logfile = lt.DbGet("LENS_MANAGER[1]", "LoggFileName", status)
    >>> Debug.Print(status)
    33

If you want to make sure that your program is working correctly you
would have to check the return status of each LightTools command that
gets executed within your program. This might be reasonable for small
scripts but is, for sure, a tedious and error prone task for larger
programs with many API function calls.

To overcome this issue, the Python interface to the LightTools API
provides builtin, automatic error handling:

.. code-block:: python

    >>> logfile = lt.DbGet("LENS_MANAGER[1]", "LoggFileName")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "E:\Repos\ltapy\ltapy\_ltapi.py", line 199, in wrapper
        return _process_return_value(lt, func_name, return_value)
      File "E:\Repos\ltapy\ltapy\_ltapi.py", line 261, in _process_return_value
        raise error.APIError(lt, status)
    ltapy.error.APIError: [33] ltStatusInvalidFunctionString:

As before, the API function call did not succeed.  But this time a
custom :class:`APIError <ltapy.error.APIError>` exception is raised
and notifys you that something went wrong. This feature eliminates the
need to check the return status of LightTools API function calls and
ensures that errors never can pass silently.

.. note::
    
    The Python interface does not use the ``status`` parameter, that
    is required by corresponding LightTools API functions. The
    ``status`` parameter has a default value of ``0`` and must not be
    provided by you.

.. _advanced-dblist-interface:

Advanced DbList() interface
---------------------------

You can access the LightTools database via the corresponding data
access functions. The ``DbList`` function together with the API
functions that operate on the object list (e.g. ``ListAtPos()``,
``ListNext()``, ``ListSize()``, ...) play a central role when you want
to loop and scan through the LightTools database.

For example, this is how you get the names of all existing solids
using the above mentioned data access functions:

.. code-block:: python

    >>> objlist = lt.DbList("COMPONENTS[1]", "SOLID")
    >>> objsize = lt.ListSize(objlist)
    >>> for i in range(objsize):
    ...     objkey = lt.ListNext(objlist)
    ...     objname = lt.DbGet(objkey, "NAME")
    ...     print(objname)
    Cube_1
    Sphere_2
    Ellipsoid_3
    Toroid_4
    Cylinder_5

With the above code, you can get your job done. But there are some
drawbacks that make things unnecessary complicated:

* You have to remember all the names of the API functions that operate
  on the object list (e.g. ``ListAtPos()``, ``ListNext()``,
  ``ListSize()``, ...).
* The code is verbose, i.e. you have to write a lot of boilerplate
  code just to get a small task done (like looping through all the
  solids in the database).
* The object list does not support direct iteration. You have to loop
  manually through the list items by using the ``range`` function.

To overcome these issues, ltapy provides an advanced ``DbList``
object. It offers a simpler and more "pythonic" interface to the
object list. Looping through the LightTools database gets as simple as
that:

.. code-block:: python

    >>> for solid in lt.DbList("COMPONENTS[1]", "SOLID"):
    ...     name = lt.DbGet(solid, "NAME")
    ...     print(name)
    Cube_1
    Sphere_2
    Ellipsoid_3
    Toroid_4
    Cylinder_5

Nice, right? The advanced ``DbList`` object is essentially a wrapper
object that replaces the original ``DbList`` function. It provides
some new functionality which is described in the following:

As seen above, you create an object list with the (wrapped) ``DbList``
API function:

.. code-block:: python

    >>> solids = lt.DbList("COMPONENTS[1]", "SOLID")

The value of the ``DbList`` object is still the (encrypted) key to the
object list. This ensures backward compatiblity to API functions that
operate on the object list:

.. code-block:: python

    >>> solids
    '@TP100039'

If you need more information you can print the contents of the object
list:

.. code-block:: python

    >>> solids.show()
    Data Key:    COMPONENTS[1]
    Filter:      SOLID
    List Key:    @TP100039
    List Items:  5 items, 0 to 4
    0     @Qs100034   Cube_1
    1     @Dh100035   Sphere_2
    2     @db100036   Ellipsoid_3
    3     @KG100037   Toroid_4
    4     @Fn100038   Cylinder_5


The builtin ``len`` function returns the size of the object list:

.. code-block:: python

    >>> len(solids)
    5

The key feature is that the ``DbList`` object now supports direct
iteration over the items of the object list:

.. code-block:: python

    >>> for solid in solids:
    ...     print(solid)
    @Qs100034
    @Dh100035
    @db100036
    @KG100037
    @Fn100038

You can conveniently access individual list elements via square
bracket notation. ``integer``, ``sclice`` or ``string`` are valid list
indices:

.. code-block:: python

    >>> solids[0]
    '@Qs100034'
    >>> solids[-1]
    '@Fn100038'
    >>> solids["Sphere_2"]
    '@Dh100035'
    >>> solids[1:]
    ['@Dh100035', '@db100036', '@KG100037', '@Fn100038']

Membership testing is also supported:

.. code-block:: python

    >>> "Toroid_4" in solids
    True

As you have seen, the ``DbList`` object provides an improved interface
to LightTools object lists and its related API functions. The whole
functionality for data access is implemented iternally which allows
you to use the object in the same way as a builtin Python container
type object.

.. note::

    Backward compatibility to the original LightTools API functions is
    given. This means that you can still pass the ``DbList`` object to
    API functions that require an object list key as input argument.
