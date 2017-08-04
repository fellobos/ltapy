import os

import pytest

from lighttools import utils


class TestVolumeScatterLogger():

    def test_filename(self, vslogger):
        default = "E:\Documents\LightTools\LTUser\TestVolRay.Log"
        assert vslogger.filename == default

        filename = "E:\Documents\LightTools\LTUser\TestVolRay.txt"
        vslogger.filename = filename
        assert vslogger.filename == filename
        vslogger.filename = default

    def test_dtype(self, vslogger):
        default = "PowerAtEvent"
        assert vslogger.dtype == default

        dtype = "ConvertedLoss"
        vslogger.dtype = dtype
        assert vslogger.dtype == dtype
        vslogger.dtype = default

    def test_xbinning(self, vslogger):
        default = (11, -1, 1)
        assert vslogger.xbinning == default

        xbinning = 51, -2.45, 0.635
        vslogger.xbinning = xbinning
        assert vslogger.xbinning == xbinning
        vslogger.xbinning = default

    def test_ybinning(self, vslogger):
        default = (11, -1, 1)
        assert vslogger.ybinning == default

        ybinning = 101, 0.815, 4.711
        vslogger.ybinning = ybinning
        assert vslogger.ybinning == ybinning
        vslogger.ybinning = default

    def test_zbinning(self, vslogger):
        default = (3, 0.5, 0.6)
        assert vslogger.zbinning == default

        zbinning = 3, 0.0, 0.75
        vslogger.zbinning = zbinning
        assert vslogger.zbinning == zbinning
        vslogger.zbinning = default

    def test_wavelength(self, vslogger):
        default = (0, 100000)
        assert vslogger.wavelength == default

        wavelength = 380, 780
        vslogger.wavelength = wavelength
        assert vslogger.wavelength == wavelength
        vslogger.wavelength = default

    def test_particle(self, vslogger):
        default = "*All"
        assert vslogger.particle == default

        particle = "L172"
        vslogger.particle = particle
        assert vslogger.particle == particle
        vslogger.particle =default

    @pytest.mark.slowtest
    def test_export(self, vslogger):
        lt = vslogger.lt
        dtype = "ConvertedLoss"
        filepath = os.path.join(utils.getcff(lt), "{}.txt".format(dtype))

        if os.path.isfile(filepath):
            os.remove(filepath)

        lt.Cmd("BeginAllSimulations")

        vslogger.export(filepath, dtype)
        assert os.path.isfile(filepath) == True

        with open(filepath) as f:
            lines = f.readlines()

        os.remove(filepath)

    def test_binvolume(self, vslogger):
        assert abs(vslogger.binvolume - 1.10192837465565E-03) < 1E-06
