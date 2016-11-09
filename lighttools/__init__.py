

__version__ = "1.0.0"


from .session import Session

from .instinfo import list_products


def installed_versions():
    """
    Return the display names of all LightTools versions that are installed
    on this computer.

    Returns:
        list of str: The display names of all installed LightTools versions.
    """
    return list_products(prefix="LightTools")
