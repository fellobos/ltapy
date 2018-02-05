"""
Utility functions for LightTools.

This module provides utility functions that are used within LightTools
and that are also useful for external consumption.
"""

def getcff(lt):
    """
    Return the folder of the current LightTools file.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Returns:
        str: The current file folder.
    """
    return lt.DbGet("LENS_MANAGER[1]", "Current File Folder")
