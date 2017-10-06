import os

import numpy as np
import pytest

import lighttools.config
import lighttools.error
import lighttools.utils

FILENAME = "ltapi.lts"
PRECISION = 1e-06


class TestGeneralUtilityFunctions:

    def test_command_processor(self, lt):
        assert lt.Cmd("wireframe") is None
        with pytest.raises(lighttools.error.APIError):
            lt.Cmd("wireframe")
        lt.Cmd("solid")

    def test_console_message_(self, lt):
        assert lt.Message("This is a test message.") is None

    def test_control_parameter(self, lt):
        assert lt.GetOption("DBUPDATE") == 1
        assert lt.SetOption("DBUPDATE", 0) is None
        lt.SetOption("DBUPDATE", 1)

    def test_expression_evaluation(self, lt):
        assert abs(lt.Eval("3.14+2") - 5.14) < PRECISION

    def test_license_status(self, lt):
        assert lt.LicenseIsAvailable("LTCore") == 1
        assert lt.LicenseIsCheckedOut("LTCore") == 1

    def test_logging(self, lt):
        cff = lighttools.utils.getcff(lt)
        logfile = os.path.join(cff, "logfile.log")
        assert lt.SetLogModeAndFilename(1, logfile) is None
        lt.SetLogModeAndFilename(0, logfile)
        if os.path.isfile(logfile):
            os.remove(logfile)

    def test_macro_code_block(self, lt):
        assert lt.Begin() is None
        assert lt.WasInterrupted() == 0
        assert lt.End() is None

    def test_scripting(self, lt):
        cff = lighttools.utils.getcff(lt)
        scriptfile = os.path.join(cff, "scriptfile.ltr")
        assert lt.SetScriptModeAndFilename(1, scriptfile) is None
        lt.SetScriptModeAndFilename(0, scriptfile)
        if os.path.isfile(scriptfile):
            os.remove(scriptfile)

    def test_session_info(self, lt):
        assert isinstance(lt.GetServerID(), int)
        assert lighttools.config.VERSION.endswith(lt.Version(0))

    def test_status_info(self, lt):
        assert isinstance(lt.GetLastMsg(1), str)
        lt.Cmd("translucent")
        lt.Cmd("solid")
        assert lt.GetStat() == 0
        with pytest.raises(lighttools.error.APIError):
            lt.Cmd("solid")
        assert lt.GetStat() == 72
        assert isinstance(lt.GetStatusString(0), str)

    def test_string_formatting(self, lt):
        assert lt.Coord2(y=3.1, z=1.7) == "ZY 1.7,3.1 "
        assert lt.Coord3(x=3.1, y=1.7, z=0.5) == "XYZ 3.1,1.7,0.5 "
        assert lt.Str("XYZ 0,0,1") == '"XYZ 0,0,1"'

    def test_user_defined_variable(self, lt):
        assert lt.SetVar("pi", 3.14) is None
        assert lt.GetVar("pi") == 3.14
        assert lt.CheckVar("pi") == 2

    def test_view_manipulation(self, lt):
        assert lt.SetActiveView("3D") is None
        assert lt.GetActiveView().startswith("3D")


class TestDataAccessFunctions:

    def test_database_access(self, lt):
        sphkey = "lens_manager[1].components[components].solid[sphere_1]"
        prmkey = (
            "lens_manager[1].components[components].solid[extrudedpolygon_5]"
            ".extrusion_primitive[extrusionprimitive_4]"
        )
        assert lt.DbSet(sphkey, "x", 2) is None
        assert lt.DbGet(sphkey, "x") == 2
        assert lt.DbSet(prmkey, "vertex_x_at", -3.14, i=2) is None
        assert lt.DbGet(prmkey, "vertex_x_at", None, i=2) == -3.14
        with pytest.raises(lighttools.error.APIError):
            lt.DbGet(sphkey, "xx")
        with pytest.raises(lighttools.error.APIError):
            lt.DbSet(sphkey, "xx", 4)

    def test_database_list(self, lt):
        compkey = "lens_manager[1].components[components]"
        solids = lt._DbList(compkey, "solid")
        assert isinstance(solids, str)
        assert isinstance(lt.ListAtPos(solids, 1), str)

        numsolids = 0
        while True:
            try:
                lt.ListNext(solids)
            except lighttools.error.APIError:
                break
            else:
                numsolids += 1
        size = lt.ListSize(solids)
        assert size == numsolids

        # Reset list pointer.
        solids = lt._DbList(compkey, "solid")

        with pytest.raises(lighttools.error.APIError):
            lt.ListAtPos(solids, size+1)
        assert isinstance(lt.ListByName(solids, "sphere_1"), str)
        assert lt.ListGetPos(solids) == 1
        assert isinstance(lt.ListNext(solids), str)
        with pytest.raises(lighttools.error.APIError):
            for i in range(size):
                lt.ListNext(solids)
        assert isinstance(lt.ListLast(solids), str)
        assert lt.ListDelete(solids) is None

    def test_database_key(self, lt):
        sphkey = "lens_manager[1].components[components].solid[sphere_1]"
        assert isinstance(lt.DbKeyDump(sphkey), str)

        compkey = "lens_manager[1].components[components]"
        solids = lt._DbList(compkey, "solid")
        assert "sphere_1" in lt.DbKeyStr(lt.ListAtPos(solids, 1)).lower()

    def test_database_type(self, lt):
        sphkey = "lens_manager[1].components[components].solid[sphere_1]"
        assert lt.DbType(sphkey, "solid") == 1
        assert lt.DbType(sphkey, "receiver") == 0

    def test_mesh_data(self, lt):
        mshkey = (
            "lens_manager[1].illum_manager[illumination_manager]"
            ".receivers[receiver_list].farfield_receiver[farfieldreceiver_2]"
            ".forward_sim_function[forward_simulation]"
            ".intensity_mesh[intensity_mesh]"
        )
        mmfkey = (
            "lens_manager[1].opt_manager[optimization_manager]"
            ".opt_meritfunctions[merit_function]"
            ".opt_meshmeritfunction[intensity_mesh]"
        )

        lng = lt.DbGet(mshkey, "x_dimension")
        lat = lt.DbGet(mshkey, "y_dimension")
        data = lt.GetMeshData(
            meshKey=mshkey,
            dataArray=np.empty((lng, lat)).tolist(),
        )
        assert abs(data.min() - lt.DbGet(mshkey, "min_value")) < PRECISION
        assert abs(data.max() - lt.DbGet(mshkey, "max_value")) < PRECISION

        target = np.random.rand(lng, lat)
        assert lt.SetMeshData(
            meshKey=mmfkey,
            dataArray=target.tolist(),
            numCols=lng,
            numRows=lat,
            cellFilter="target",
        ) is None
        assert np.allclose(
            a=lt.GetMeshData(
                meshKey=mmfkey,
                dataArray=np.empty((lng, lat)).tolist(),
                cellFilter="target",
            ),
            b=target,
            atol=PRECISION,
        )

    def test_freeform_surface_points(self, lt):
        ffskey = (
            "lens_manager[1].components[components].solid[freeformentity_7]"
            ".freeform_primitive[freeformprimitive_1]"
            ".freeform_surface[frontsurface]"
        )

        u = lt.DbGet(ffskey, "numpointsinu")
        v = lt.DbGet(ffskey, "numpointsinv")

        data = lt.GetFreeformSurfacePoints(
            surfaceKey=ffskey,
            surfacePoints=np.empty((u, v, 3)).tolist(),
        )
        assert abs(data[0,0,0] - -8.548375913185581) < PRECISION
        assert abs(data[-1,-1,-1] - -4.274187956592790) < PRECISION

        data[:,:,-1] -= 1
        assert lt.SetFreeformSurfacePoints(
            surfaceKey=ffskey,
            surfacePoints=data.tolist(),
            numPointsU=u,
            numPointsV=v,
        ) is None
        assert np.allclose(
            a=lt.GetFreeformSurfacePoints(
                surfaceKey=ffskey,
                surfacePoints=np.empty((u, v, 3)).tolist(),
            ),
            b=data,
            atol=PRECISION,
        )

    def test_mesh_strings(self, lt):
        fwskey = (
            "lens_manager[1].illum_manager[illumination_manager]"
            ".receivers[receiver_list].farfield_receiver[farfieldreceiver_2]"
            ".forward_sim_function[forward_simulation]"
        )
        lt.Cmd("beginallsimulations")
        numpaths = lt.DbGet(fwskey, "numberofraypaths")
        data = lt.GetMeshStrings(
            meshKey=fwskey,
            stringArray=np.empty((1, numpaths), dtype=np.str).tolist(),
            cellFilter="raypathstringat",
        )
        assert "pointSource_3" in data[0,0]

        assert lt.SetMeshStrings(
            meshKey=fwskey,
            stringArray=np.random.choice(["yes", "no"], numpaths).tolist(),
            numCols=1,
            numRows=numpaths,
            cellFilter="raypathvisibleat",
        ) is None

    def test_receiver_ray_data(self, lt):
        fwskey = (
            "lens_manager[1].illum_manager[illumination_manager]"
            ".receivers[receiver_list].farfield_receiver[farfieldreceiver_2]"
            ".forward_sim_function[forward_simulation]"
        )
        numrays = 10
        items = ["raydatax", "raydatay", "raydatawavelength"]
        data = lt.GetReceiverRayData(
            receiverKey=fwskey,
            dataDescriptors=items,
            data=np.empty((numrays, len(items))).tolist(),
            startingRay=1,
            numberOfRays=numrays,
        )
        assert data[0,-1] == 550

    def test_swept_profile_points(self, lt):
        sptkey = (
            "lens_manager[1].components[components].solid[sweptentity_10]"
            ".swept_primitive[sweptprimitive_5]"
        )
        numpoints = lt.DbGet(sptkey, "numpoints")
        data = lt.GetSweptProfilePoints(
            profileKey=sptkey,
            profilePoints=np.empty((numpoints, 2)).tolist(),
        )
        assert abs(data[0,-1] - -10.30970563978885) < PRECISION

        data[0,-1] = -15
        assert lt.SetSweptProfilePoints(
            profileKey=sptkey,
            profilePoints=data.tolist(),
            numPoints=numpoints,
        ) is None
        assert np.allclose(
            a=lt.GetSweptProfilePoints(
                profileKey=sptkey,
                profilePoints=np.empty((numpoints, 2)).tolist()
            ),
            b=data,
            atol=PRECISION,
        )


class TestSpecialProcessingFunctions:

    def test_color_matching_functions(self, lt):
        wv = 550
        assert abs(lt.GetCIE1931XBar(wv) - 0.4334499) < PRECISION
        assert abs(lt.GetCIE1931YBar(wv) - 0.9949501) < PRECISION
        assert abs(lt.GetCIE1931ZBar(wv) - 0.0087499) < PRECISION

    def test_spectral_efficiency_functions(self, lt):
        wv = 550
        assert abs(lt.GetPhotopicFunction(wv) - 0.994950) < PRECISION
        assert abs(lt.GetScotopicFunction(wv) - 0.481) < PRECISION

    def test_quick_ray(self, lt):
        srfkey = (
            "lens_manager[1].components[components].solid[cylinder_6]"
            ".cylinder_primitive[cylinderprimitive_1]"
            ".cylinder_surface[cylindersurface]"
        )

        # Trace a non-sequential ray starting at the global origin,
        # with a -45 degree angle.
        numhits, data = lt.QuickRayAim(
            rayVec=[0, 0, 0, 0, -1, 1],
            surfKey=srfkey,
            outVec=np.empty((10)).tolist(),
        )
        assert numhits == 2

        numhits, data = lt.QuickRayQuery(
            segId=numhits,
            surfKey=srfkey,
            outVec=np.empty((10)).tolist(),
        )
        angle_of_exit = data[-1]
        assert abs(angle_of_exit - 45) < PRECISION

    def test_spline_patch(self, lt):
        srfkey = (
            "lens_manager[1].components[components].solid[lens_11]"
            ".circ_lens_primitive[lp_2]"
            ".splinepatch_lens_surface[lensrearsurface]"
        )

        u = lt.DbGet(srfkey, "numpointsinu")
        v = lt.DbGet(srfkey, "numpointsinv")

        data = lt.GetSplineData(
            surfKey=srfkey,
            dataArray=np.empty((u, v, 3)).tolist(),
        )
        assert abs(data[0,0,0] - -10.1) < PRECISION
        assert abs(data[2,1,0] - 3.3666667) < PRECISION

        data[:,:,-1] = np.random.rand(u, v) * 10
        assert lt.SplinePatch(
            surfKey=srfkey,
            dataArray=data.tolist(),
            numPointsU=u,
            numPointsV=v
        ) is None
        assert np.allclose(
            a=lt.GetSplineData(
                surfKey=srfkey,
                dataArray=np.empty((u, v, 3)).tolist(),
            ),
            b=data,
            atol=PRECISION,
        )

    def test_spline_sweep(self, lt):
        srfkey = (
            "lens_manager[1].components[components].solid[lens_12]"
            ".circ_lens_primitive[lp_3]"
            ".splinesweep_lens_surface[lensrearsurface]"
        )

        numpoints = 5

        data = lt.GetSplineData(
            surfKey=srfkey,
            dataArray=np.empty((numpoints, 2)).tolist()
        )
        assert abs(data[-1,0] - 7.575) < PRECISION

        data[:,-1] = np.random.rand(numpoints) * -5
        lt.SplineSweep(
            surfKey=srfkey,
            dataArray=data.tolist(),
            numPoints=numpoints,
        )
        assert np.allclose(
            a=lt.GetSplineData(
                surfKey=srfkey,
                dataArray=np.empty((numpoints, 2)).tolist()
            ),
            b=data,
            atol=PRECISION,
        )

        data = lt.GetSplineVec(
            surfKey=srfkey,
            startEndFlag=1,
            tanVec=np.empty((2,)).tolist(),
        )
        data[0] -= 0.1
        lt.SetSplineVec(
            surfKey=srfkey,
            startEndFlag=1,
            tanVec=data.tolist(),
        )
        assert np.allclose(
            a=lt.GetSplineVec(
                surfKey=srfkey,
                startEndFlag=1,
                tanVec=np.empty((2,)).tolist()
            ),
            b=data,
            atol=PRECISION,
        )


class TestViewAccessFunctions:

    def test_console_view(self, lt):
        key = lt.ViewKey("VIEW[0]")
        assert key.startswith("@")
        assert isinstance(lt.ViewKeyDump(key), str)
        assert lt.ViewGet(key, "title") == "Console"

    def test_3D_design_view(self, lt):
        key = lt.ViewKey("VIEW[1]")
        assert key.startswith("@")
        assert isinstance(lt.ViewKeyDump(key), str)
        assert lt.ViewGet(key, "ucsdisplaystyle") == "OpenArrowHead"
        lt.ViewSet(key, "ucsdisplaystyle", "planes")
        assert lt.ViewGet(key, "ucsdisplaystyle") == "Planes"
