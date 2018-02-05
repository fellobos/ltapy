"""
This module provides utility functions, useful for external consumption.
"""

import numpy as np


def binspace(num, start, stop):
    """
    Return evenly spaced bin midpoints over the given interval.

    Calculate `num` evenly spaced bin midpoints over the closed interval
    [`start`, `stop`].

    Args:
        num (int): Number of bin midpoints to generate. Must be positive.
        start (float): The starting value of the interval.
        stop (float): The end value of the interval.

    Returns:
        numpy.ndarray: `num` equally spaced bin midpoints in the interval
            [`start`, `stop`].

    Examples:
        >>> bins = binspace(11, -1, 1)
        >>> bins
        array([ -9.09090909e-01,  -7.27272727e-01,  -5.45454545e-01,
                -3.63636364e-01,  -1.81818182e-01,   8.32667268e-17,
                 1.81818182e-01,   3.63636364e-01,   5.45454545e-01,
                 7.27272727e-01,   9.09090909e-01])
    """
    samples, step = np.linspace(start, stop, num+1, retstep=True)
    samples += 0.5 * step
    return samples[:-1]


def get_current_file_folder(lt):
    """
    Return the folder of the current LightTools file.

    Args:
        ltapi (ILTAPIx): A handle to the LightTools session.

    Returns:
        str: The file folder of the current LightTools file.
    """
    return lt.DbGet("LENS_MANAGER[1]", "Current File Folder")
