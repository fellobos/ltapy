"""
Query product installation data from the Windows registry.

The installation data of (most) programs is stored under the
`Uninstall` registry key. Also the LightTools installer stores its
installation data there. This module provides methods to query product
information like name, version or install location from this registry
key.
"""

import winreg

# Installation data is stored under the `Uninstall` registry key.
HKEY_UNINSTALL = winreg.OpenKeyEx(
    winreg.HKEY_LOCAL_MACHINE,
    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
)


def list_products(prefix=None, sort=True):
    """
    Return the display names of installed products.

    Args:
        prefix (str, optional): List only those products whose display
            names start with the given `prefix`. If None, return the
            display names of all installed products.
        sort (bool, optional): Return an alphabetically sorted version of
            the products list.

    Returns:
        list of str: The display names of the found products.

    Examples:
        Get the display names of all LightTools products that are
        installed on this computer:

        >>> products = list_products(prefix="LightTools")
        >>> products
        ['LightTools(64) 8.3.2', 'LightTools(64) 8.4.0']
    """
    products = []

    for hkey in subkeys(HKEY_UNINSTALL):
        value_data, value_type = query_value(hkey, "DisplayName")
        # Don't include products that have no display name property.
        if not value_data:
            continue
        if prefix and not value_data.startswith(prefix):
            continue
        products.append(value_data)

    if sort:
        products.sort()

    return products


def subkeys(hkey):
    """
    A generator that iterates over the subkeys of the given registry key.

    Args:
        hkey (PyHKEY): An already open registry key, or one of the
            predefined winreg.HKEY_* constants.

    Yields:
        PyHKEY: An already open subkey.
    """
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(hkey, i)
        except OSError:  # Raised if no more values are available.
            break
        else:
            yield winreg.OpenKeyEx(hkey, subkey)
        i += 1


def values(hkey):
    """
    A generator that iterates over the values of the given registry key.

    Args:
        hkey (PyHKEY): An already open registry key, or one of the
            predefined winreg.HKEY_* constants.

    Yields:
        tuple: Name and data property of the value.
    """
    i = 0
    while True:
        try:
            value_name, value_data, value_type = winreg.EnumValue(hkey, i)
        except OSError:  # Raised if no more values are available.
            break
        else:
            yield (value_name, value_data)
        i += 1


def query_value(hkey, value_name):
    """
    Query value data and value type from the given registry key.

    Args:
        hkey (PyHKEY): An already open registry key, or one of the
            predefined winreg.HKEY_* constants.
        value_name (str): The name property of the value.

    Returns:
        tuple: The value data and value type of the registry item. Return
            (None, None) if the registry key does not have the requested
            value.
    """
    try:
        value_data, value_type = winreg.QueryValueEx(hkey, value_name)
    except OSError:  # The registry key might not have the specified value.
        return None, None
    else:
        return value_data, value_type


def query(product):
    """
    Query the installation data for the given product.

    Args:
        product (str): The display name of the product for which the
            installation data should be queried.

    Returns:
        dict: A mapping that contains the product installation data as
            `value_name`: `value_data` pairs.

    Raises:
        ValueError: If the installation data for the program could not be
            found.

    Examples:
        Query the Windows registry for the installation data of the
        program 'Lighttools v8.4.0':

        >>> install_data = query(product="LightTools(64) 8.4.0")
        >>> install_data
        {'AuthorizedCDFPrefix': '',
         'Comments': '',
         'Contact': '',
         'DisplayName': 'LightTools(64) 8.4.0',
         'DisplayVersion': '8.4.2.1',
         ...
         ...
         ...
         'VersionMajor': 8,
         'VersionMinor': 4,
         'WindowsInstaller': 1}

    """
    for hkey in subkeys(HKEY_UNINSTALL):
        value_data, value_type = query_value(hkey, "DisplayName")
        if value_data == product:
            install_data = {}
            for value_name, value_data in values(hkey):
                install_data[value_name] = value_data
            return install_data
    else:
        msg = ("Could not find installation data for product {!r}.")
        raise ValueError(msg.format(product))
