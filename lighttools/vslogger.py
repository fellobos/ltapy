"""
Provide an interface to the LightTools Volume Scatter Logger utility.
"""

from . import error


class VolumeScatterLogger():

    """
    Interface to the LightTools Volume Scatter Logger utility.

    Args:
        lt (ILTAPIx): A handle to the LightTools session.
        key (str): The data access key of the Volume Scatter Logger.

    Attributes:
        lt (ILTAPIx): A handle to the LightTools session.
        key (str): The data access key of the Volume Scatter Logger.

    Examples:
        Connect to a volume scatter logger attached to a solid object with 
        scattering material.

        >>> key = (
                "SOLID[Phosphor].VOLUME_INTERFACE[VolumeInterface_EOS]"
                ".VOLUME_SCATTER_LOG[VolumeScatterLog]"
            )
        >>> vslogger = VolumeScatterLogger(lt, key)

        Set number of bins and domain size along global axes.

        >>> vslogger.xbinning = (11, -1, 1)
        >>> vslogger.ybinning = (11, -1, 1)
        >>> vslogger.zbinning = (3, 0, 0.07)

        Export the binned conversion loss data to a file.

        >>> vslogger.export(dtype="ConvertedLoss")
    """

    def __init__(self, lt, key):
        self.lt = lt
        self.key = key

    @property
    def filename(self):
        """
        str: Filepath for logging (used for 3D data export).
        """
        return self._get_value(index=1)

    def _get_value(self, index):
        """
        Return the value of a specific volume scatter parameter.

        Args:
            index (int): The parameter's list index.

        Returns:
            value: The parameter's value.
        """
        return self.lt.DbGet(self.key, "StringAttributeAt", None, index)

    @filename.setter
    def filename(self, value):
        self._set_value(value, index=1)

    def _set_value(self, value, index):
        """
        Set the value of a specific volume scatter parameter.

        Args:
            value: The value of the parameter.
            index (int): The parameter's list index.
        """
        self.lt.DbSet(self.key, "StringAttributeAt", value, index)

    @property
    def dtype(self):
        """
        str: Data type for file export. 
        """
        return self._get_value(index=5)

    @dtype.setter
    def dtype(self, value):
        self._set_value(value, index=5)

    @property
    def xbinning(self):
        """
        tuple: Number of bins and domain size along global X-axis,
            e.g. (numx, minx, maxx).
        """
        return self._get_binning(index=6)

    def _get_binning(self, index):
        """
        Return binning data for a specific axis.

        Args:
            index: The list index of the requested axis.

        Returns:
            tuple: Binning data given as number of bins and domain size along
                the requested axis, e.g. (numx, minx, maxx).
        """
        binning = self._get_value(index)
        num, min_, max_ = binning.split(",")
        return int(num), float(min_), float(max_)

    @xbinning.setter
    def xbinning(self, values):
        self._set_binning(values, index=6)

    def _set_binning(self, values, index):
        """
        Set binning data for a specific axis.

        Args:
            values (int, float, float): Binning data.
            index: The list index of the requested axis.
        """
        num, min_, max_ = values
        value = ",".join(
            [str(x) for x in (int(num), float(min_), float(max_))]
        )
        self._set_value(value, index)

    @property
    def ybinning(self):
        """
        tuple: Number of bins and domain size along global Y-axis,
            e.g. (numy, miny, maxy).
        """
        return self._get_binning(index=7)

    @ybinning.setter
    def ybinning(self, values):
        self._set_binning(values, index=7)

    @property
    def zbinning(self):
        """
        tuple: Number of bins and domain size along global Z-axis,
            e.g. (numz, minz, maxz).
        """
        return self._get_binning(index=8)

    @zbinning.setter
    def zbinning(self, values):
        self._set_binning(values, index=8)

    @property
    def wavelength(self):
        """
        tuple: Wavelength limits in nanometers, e.g. (min_wv, max_wv).
        """
        limits = self._get_value(index=11)
        min_, max_ = limits.split(",")
        return int(min_), int(max_)

    @wavelength.setter
    def wavelength(self, values):
        min_, max_ = values
        value = ",".join([str(x) for x in (int(min_), int(max_))])
        self._set_value(value, index=11)        

    @property
    def particle(self):
        """
        str: Particle filter name for capturing of events.
        """
        return self._get_value(index=12)

    @particle.setter
    def particle(self, value):
        self._set_value(value, index=12)

    def export(self, filepath=None, dtype=None):
        self._form_open()
        if filepath:
            self.filename = filepath
        if dtype:
            self.dtype = dtype
        self._form_export()
        self._form_close()

    def _form_open(self):
        """
        Open the form.
        """
        self._form_call("O")

    def _form_call(self, value):
        """
        Interact with the associated form.

        Automation of the form (open/close, data export) is possible via
        the 3rd parameter.
        """
        try:
            self._set_value(value, index=3)
        except error.APIError:
            pass

    def _form_export(self):
        """
        Write 3D bin data to file.
        """
        self._form_call("E")

    def _form_close(self):
        """
        Close the form.
        """
        self._form_call("C")

    @property
    def binvolume(self):
        """
        float: Volume of a single bin.
        """
        numx, minx, maxx = self.xbinning
        numy, miny, maxy = self.ybinning
        numz, minz, maxz = self.zbinning
        dx = (maxx-minx) / numx
        dy = (maxy-miny) / numy
        dz = (maxz-minz) / numz
        return dx * dy * dz
