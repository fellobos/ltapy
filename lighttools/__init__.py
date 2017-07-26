

__version__ = "1.0.0"


# TODO: Big namespace cleanup
#   - Import only frequently used classes and functions to global namespace
#     (e.g. lts.Session(), lts.config, lts.binspace(), ...)
#   - Delete names of imported modules with del statement from global
#     namespace
#   - In public modules (e.g. apodization.py), hide non-public objects
#     from namespace with "_" prefix. The same is true for imported module
#     objects, e.g. import os as _os.


from .session import Session
from .instinfo import list_products

from . import apodization

def installed_versions():
    """
    Return the display names of all LightTools versions that are installed
    on this computer.

    Returns:
        list of str: The display names of all installed LightTools versions.
    """
    return list_products(prefix="LightTools")
