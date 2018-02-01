import collections
import os
import string
import tempfile

import pandas as pd
from win32com.client import constants as LTReturnCodeEnum

import lighttools.error


class DbKey(str):

    def __new__(cls, ltapi, key, *args, **kwargs):
        return str.__new__(cls, key)

    def __init__(self, ltapi, key):
        self._key = key
        self._ltapi = ltapi
        self._dump()
        self.__doc__ = self._buffer

    def __getattribute__(self, attr):
        if attr.startswith("_"):
            return object.__getattribute__(self, attr)
        elif hasattr(str(), attr):
            return super(DbKey, self).__getattribute__(attr)
        else:
            return self._ltapi.DbGet(self._key, attr)

    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            object.__setattr__(self, attr, value)
        elif attr == "key":
            raise AttributeError("data key attribute is read-only.")
        else:
            self._ltapi.DbSet(self._key, attr, value)

    # def __str__(self):
    #     return self._buffer

    def _dump(self):
        self._write_dump_file()
        self._update_class_dict()
        self._save_dump_file_to_buffer()
        self._delete_dump_file()

    def _write_dump_file(self):
        self._tmpfile = tempfile.NamedTemporaryFile(delete=False)
        self._ltapi.DbKeyDump(self._key, self._tmpfile.name)
        self._tmpfile.close()

    def _update_class_dict(self):
        # Note: Depending on the data key the dump file can have 3 or 4 columns.
        df = pd.read_csv(
            self._tmpfile.name, sep="\s\s+", skiprows=4, header=None,
            engine="python"
        )
        df[0] = df[0].str.replace(" ", "_").str.lower()
        for attr in df[0]:
            self.__dict__[attr] = None

    def _save_dump_file_to_buffer(self):
        with open(self._tmpfile.name) as f:
            self._buffer = "\n".join(line.strip() for line in f.readlines())

    def _delete_dump_file(self):
        os.remove(self._tmpfile.name)


class DbList(str):

    """
    An enhanced DbList object that offers a pythonic interface to the
    database list.

    The object provides a more comfortable (and pythonic) way to work with
    the database list. It behaves like a built-in container type object
    and enables full access to the contents of the database list (via its
    associated container type methods). The object can therefore be used
    as full replacement for all the API methods that operate on the
    database list (e.g. ListAtPos, ListByName, ...). For example, the
    object supports direct looping over the database list and individual
    list elements can be accessed via square bracket notation. See the
    Examples section below for further information.

    Compatibility to the database list API functions is given. This means
    that the DbList object can still be passed to API functions that
    require a database list key as input argument.

    Args:
        ltapi (ILTAPIx): Handle to the LightTools session.
        datakey (str): The root database item for the list.
        filter_ (str): Specifies what type of objects to put into the
            list.

    Examples:
        Create a DbList object (as usual) with the DbList() API function.

        >>> solids = lt.DbList("COMPONENTS[1]", "SOLID")

        Use the string representation of the object to get more info about
        the database list.

        >>> solids
        <class 'lighttools.core.dbaccess.DbList'>
        Data key: COMPONENTS[1]
        Filter:   SOLID
        List key: @NL100015, 3 items, 0 to 2
        List items:
        0     @Lx100012   Cube_4
        1     @wt100013   Sphere_5
        2     @Ix100014   Cylinder_6

        The value of the object (inherited from str) holds the database
        list key. This object behaviour ensures compatiblity with the
        corresponding database list API functions (e.g. ListAtPos,
        ListByName, ...).

        >>> print(solids)
        @NL100015

        The len() function returns the size of the database list.

        >>> len(solids)
        3

        Direct iteration over the database list items is supported.

        >>> for solid in solids:
        >>>    print(solid)
        @Lx100012
        @wt100013
        @Ix100014

        Individual list elements can conveniently be accessed via square
        bracket notation. Valid list indices are integers, slices or str.

        >>> solids[0]
        '@Lx100012'
        >>> solids[-1]
        @Ix100014
        >>> solids["Sphere_5"]
        @wt100013
        >>> solids[1:]
        ['@wt100013', '@Ix100014']

        Membership testing is also possible (the names of the database
        list items are considered).

        >>> "Cube_4" in solids
        True
    """

    def __new__(cls, ltapi, datakey, filter_):
        # Objects of type str are immutable. Their value cannot be
        # initialized (as usual) in the __init__ method. Because the value
        # of listkey is not known before object creation the __new__ method
        # of str must be overriden.
        listkey = ltapi._DbList(dataKey=datakey, filter=filter_)
        return super().__new__(cls, listkey)

    def __init__(self, ltapi, datakey, filter_):
        self.ltapi = ltapi
        self.datakey = datakey
        self.filter = filter_

    def __del__(self):
        self.ltapi.ListDelete(listKey=self)

    def show(self):
        """
        Show the contents of the database list.
        """
        s = "Data key:   {}\n".format(self.datakey)
        s += "Filter:     {}\n".format(self.filter)
        size = self.ltapi.ListSize(self)
        s += "List key:   {}\n".format(self)
        s += "List items: {} items, {} to {}\n".format(size, 0, size-1)
        for i, key in enumerate(self):
            name = self.ltapi.DbGet(key, "NAME")
            s += "{:<4}  {:<10s}  {}\n".format(i, key, name)
        print(s)

    def __len__(self):
        return self.ltapi.ListSize(listKey=self)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.ltapi.ListByName(listKey=self, dataName=key)
        elif isinstance(key, int):
            if key < 0:
                key += self.ltapi.ListSize(listKey=self)
            return self.ltapi.ListAtPos(listKey=self, positionOfList=key+1)
        elif isinstance(key, slice):
            size = self.ltapi.ListSize(listKey=self)
            items = [
                self.ltapi.ListAtPos(listKey=self, positionOfList=i+1)
                for i in range(size)
            ]
            return items[key]
        else:
            msg = "{} indices must be integer, slice or str, not {}."
            name = self.__class__.__name__
            raise TypeError(msg.format(name, repr(type(key))))

    def __iter__(self):
        try:
            self.ltapi.ListSetPos(listKey=self, positionOfList=1)
        except lighttools.error.APIError as e:
            if (e.status == LTReturnCodeEnum.ltStatusListIsEmpty
                or e.status == LTReturnCodeEnum.ltStatusInvalidListPosition):
                pass
            else:
                raise
        return self

    def __contains__(self, item):
        try:
            datakey = self.ltapi.ListByName(listKey=self, dataName=item)
        except lighttools.error.APIError:
            return False
        else:
            return True

    def __next__(self):
        try:
            return self.ltapi.ListNext(listKey=self)
        except lighttools.error.APIError as e:
            if (e.status == LTReturnCodeEnum.ltStatusListIsEmpty
                or e.status == LTReturnCodeEnum.ltStatusEndOfList):
                raise StopIteration
            else:
                raise
