# -*- coding: utf-8 -*-

"""
Simplified access to the LightTools database.
"""

from win32com.client import constants as LTReturnCodeEnum

import lighttools.error


class DbList(str):

    """
    A 'pythonic' interface to a LightTools database list.

    Provide a simpler and more 'pythonic' way to work with LightTools
    database lists.  The object behaves like a builtin Python container
    type object and enables full access to the contents of the database
    list.  It can therefore be used as full replacement for all the API
    methods that operate on the database list (e.g. ListAtPos, ListByName,
    ...).  For example, the object supports direct looping over the
    database list and, furthermore, individual list elements can be
    accessed via square bracket notation.  See the Examples section below
    for more information.

    Compatibility to the database list API functions is given.  This means
    that you can pass the DbList class to API functions that require a
    database list key as input argument.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
        datakey (str): The root database item for the list.
        filter_ (str): Specifies what type of objects to put into the
            list.

    Examples:
        Create a DbList object, as usual, with the DbList() API function.

        >>> solids = lt.DbList(
        ...     "LENS_MANAGER[1].COMPONENTS[Components]", "SOLID"
        ... )

        Use the string representation of the object to get more info about
        the database list.

        >>> solids
        Data Key:    LENS_MANAGER[1].COMPONENTS[Components]
        Filter:      SOLID
        List Key:    @UE100398
        List Items:  5 items, 0 to 4
        0     @iS100393   Cube_1
        1     @UT100394   Sphere_2
        2     @Ag100395   Ellipsoid_3
        3     @Ev100396   Toroid_4
        4     @bd100397   Cylinder_5

        The value of the object (inherited from str) holds the database
        list key.  This ensures compatiblity with the corresponding
        database list API functions (e.g. ListAtPos, ListByName, ...).

        >>> print(solids)
        @UE100398

        The len() function returns the size of the database list.

        >>> len(solids)
        5

        Direct iteration over the database list items is supported.

        >>> for solid in solids:
        >>>    print(solid)
        @iS100393
        @UT100394
        @Ag100395
        @Ev100396
        @bd100397

        Individual list elements can conveniently be accessed via square
        bracket notation.  Valid list indices are integers, slices or str.

        >>> solids[0]
        '@Zm100407'
        >>> solids[-1]
        '@dk100411'
        >>> solids["Sphere_2"]
        '@Qp100408'
        >>> solids[1:]
        ['@Qp100408', '@kg100409', '@FR100410', '@dk100411']

        Membership testing is also possible.  The names of the database
        list items are considered.

        >>> "Toroid_4" in solids
        True
    """

    def __new__(cls, lt, datakey, filter_):
        # Objects of type str are immutable.  Their value cannot be
        # initialized as usual in the __init__ method.  Because the value
        # of listkey is not known before object creation the __new__ method
        # of str must be overriden.
        listkey = lt._DbList(dataKey=datakey, filter=filter_)
        return super().__new__(cls, listkey)

    def __init__(self, lt, datakey, filter_):
        self._lt = lt
        self._datakey = datakey
        self._filter = filter_

    def show(self):
        """
        Print the contents of the database list.
        """
        # Note: It is not possible to use __repr__ for displaying the contents
        # of the database list because the logging calls that are attached to
        # the functions in __repr__ lead to infinite recursion.
        s = "Data Key:    {}\n".format(self._datakey)
        s += "Filter:      {}\n".format(self._filter)
        size = self._lt.ListSize(self)
        s += "List Key:    {}\n".format(self)
        s += "List Items:  {} items, {} to {}".format(size, 0, size-1)
        for i, key in enumerate(self):
            name = self._lt.DbGet(key, "NAME")
            s += "\n{:<4}  {:<10s}  {}".format(i, key, name)
        print(s)

    def __len__(self):
        return self._lt.ListSize(listKey=self)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._lt.ListByName(listKey=self, dataName=key)
        elif isinstance(key, int):
            if key < 0:
                key += self._lt.ListSize(listKey=self)
            return self._lt.ListAtPos(listKey=self, positionOfList=key+1)
        elif isinstance(key, slice):
            size = self._lt.ListSize(listKey=self)
            items = [
                self._lt.ListAtPos(listKey=self, positionOfList=i+1)
                for i in range(size)
            ]
            return items[key]
        else:
            msg = "{} indices must be integer, slice or str, not {}."
            name = self.__class__.__name__
            raise TypeError(msg.format(name, repr(type(key))))

    def __iter__(self):
        try:
            self._lt.ListSetPos(listKey=self, positionOfList=1)
        except lighttools.error.APIError as e:
            if (e.status == LTReturnCodeEnum.ltStatusListIsEmpty
                or e.status == LTReturnCodeEnum.ltStatusInvalidListPosition):
                pass
            else:
                raise
        return self

    def __contains__(self, item):
        try:
            self._lt.ListByName(listKey=self, dataName=item)
        except lighttools.error.APIError:
            return False
        else:
            return True

    def __next__(self):
        try:
            return self._lt.ListNext(listKey=self)
        except lighttools.error.APIError as e:
            if (e.status == LTReturnCodeEnum.ltStatusListIsEmpty
                or e.status == LTReturnCodeEnum.ltStatusEndOfList):
                raise StopIteration
            else:
                raise
