import os

import numpy as np
import pytest

import lighttools.config
import lighttools.error
import lighttools.utils

FILENAME = "ltapi.lts"
PRECISION = 1e-6


class TestGeneralUtilityFunctions:

    def test_command_processor(self, lt):
        assert lt.Cmd("Wireframe") is None
        with pytest.raises(lighttools.error.APIError):
            lt.Cmd("Wireframe")
        lt.Cmd("Solid")

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
        lt.Cmd("Translucent")
        lt.Cmd("Solid")
        assert lt.GetStat() == 0
        with pytest.raises(lighttools.error.APIError):
            lt.Cmd("Solid")
        assert lt.GetStat() == 72
        assert isinstance(lt.GetStatusString(0), str)

    def test_string_formatting(self, lt):
        assert lt.Coord2(y=3.1, z=1.7) == "ZY 1.7,3.1 "
        assert lt.Coord3(x=3.1, y=1.7, z=0.5) == "XYZ 3.1,1.7,0.5 "
        assert lt.Str("XYZ 0,0,1") == '"XYZ 0,0,1"'

    def test_user_defined_variable(self, lt):
        assert lt.SetVar("PI", 3.14) is None
        assert lt.GetVar("PI") == 3.14
        assert lt.CheckVar("PI") == 2

    def test_view_manipulation(self, lt):
        assert lt.SetActiveView("3D") is None
        assert lt.GetActiveView().startswith("3D")


class TestDataAccessFunctions:

    def test_database_access(self, lt):
        sphkey = "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Sphere_1]"
        prmkey = (
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[ExtrudedPolygon_5]"
            ".EXTRUSION_PRIMITIVE[ExtrusionPrimitive_4]"
        )
        assert lt.DbSet(sphkey, "X", 2) is None
        assert lt.DbGet(sphkey, "X") == 2
        assert lt.DbSet(prmkey, "Vertex_X_At", -3.14, i=2) is None
        assert lt.DbGet(prmkey, "Vertex_X_At", None, i=2) == -3.14
        with pytest.raises(lighttools.error.APIError):
            lt.DbGet(sphkey, "XX")
        with pytest.raises(lighttools.error.APIError):
            lt.DbSet(sphkey, "XX", 4)

    def test_database_list(self, lt):
        compkey = "LENS_MANAGER[1].COMPONENTS[Components]"
        solids = lt._DbList(compkey, "SOLID")
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
        solids = lt._DbList(compkey, "SOLID")

        with pytest.raises(lighttools.error.APIError):
            lt.ListAtPos(solids, size+1)
        assert isinstance(lt.ListByName(solids, "Sphere_1"), str)
        assert lt.ListGetPos(solids) == 1
        assert isinstance(lt.ListNext(solids), str)
        with pytest.raises(lighttools.error.APIError):
            for i in range(size):
                lt.ListNext(solids)
        assert isinstance(lt.ListLast(solids), str)
        assert lt.ListDelete(solids) is None

    def test_database_key(self, lt):
        sphkey = "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Sphere_1]"
        assert isinstance(lt.DbKeyDump(sphkey), str)

        compkey = "LENS_MANAGER[1].COMPONENTS[Components]"
        solids = lt._DbList(compkey, "SOLID")
        assert "Sphere_1" in lt.DbKeyStr(lt.ListAtPos(solids, 1))

    def test_database_type(self, lt):
        sphkey = "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Sphere_1]"
        assert lt.DbType(sphkey, "SOLID") == 1
        assert lt.DbType(sphkey, "RECEIVER") == 0

    def test_mesh_data(self, lt):
        mshkey = (
            "LENS_MANAGER[1].ILLUM_MANAGER[Illumination_Manager]"
            ".RECEIVERS[Receiver_List].FARFIELD_RECEIVER[farFieldReceiver_2]"
            ".FORWARD_SIM_FUNCTION[Forward_Simulation]"
            ".INTENSITY_MESH[Intensity_Mesh]"
        )
        mmfkey = (
            "LENS_MANAGER[1].OPT_MANAGER[Optimization_Manager]"
            ".OPT_MERITFUNCTIONS[Merit_Function]"
            ".OPT_MESHMERITFUNCTION[Intensity_Mesh]"
        )

        lng = int(lt.DbGet(mshkey, "X_Dimension"))
        lat = int(lt.DbGet(mshkey, "Y_Dimension"))
        data = lt.GetMeshData(
            meshKey=mshkey,
            dataArray=np.empty((lng, lat)).tolist(),
        )
        assert abs(data.min() - lt.DbGet(mshkey, "Min_Value")) < PRECISION
        assert abs(data.max() - lt.DbGet(mshkey, "Max_Value")) < PRECISION

        target = np.random.rand(lng, lat)
        assert lt.SetMeshData(
            meshKey=mmfkey,
            dataArray=target.tolist(),
            numCols=lng,
            numRows=lat,
            cellFilter="Target",
        ) is None
        assert np.allclose(
            a=lt.GetMeshData(
                meshKey=mmfkey,
                dataArray=np.empty((lng, lat)).tolist(),
                cellFilter="Target",
            ),
            b=target,
            atol=PRECISION,
        )

    def test_freeform_surface_points(self, lt):
        ffskey = (
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[FreeformEntity_7]"
            ".FREEFORM_PRIMITIVE[FreeformPrimitive_1]"
            ".FREEFORM_SURFACE[FrontSurface]"
        )

        u = int(lt.DbGet(ffskey, "NumPointsInU"))
        v = int(lt.DbGet(ffskey, "NumPointsInV"))

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
            "LENS_MANAGER[1].ILLUM_MANAGER[Illumination_Manager]"
            ".RECEIVERS[Receiver_List].FARFIELD_RECEIVER[farFieldReceiver_2]"
            ".FORWARD_SIM_FUNCTION[Forward_Simulation]"
        )
        lt.Cmd("BeginAllSimulations")
        numpaths = int(lt.DbGet(fwskey, "NumberOfRayPaths"))
        data = lt.GetMeshStrings(
            meshKey=fwskey,
            stringArray=np.empty((1, numpaths), dtype=np.str).tolist(),
            cellFilter="RayPathStringAt",
        )
        assert "pointSource_3" in data[0,0]

        assert lt.SetMeshStrings(
            meshKey=fwskey,
            stringArray=np.random.choice(["Yes", "No"], numpaths).tolist(),
            numCols=1,
            numRows=numpaths,
            cellFilter="RayPathVisibleAt",
        ) is None

    def test_receiver_ray_data(self, lt):
        fwskey = (
            "LENS_MANAGER[1].ILLUM_MANAGER[Illumination_Manager]"
            ".RECEIVERS[Receiver_List].FARFIELD_RECEIVER[farFieldReceiver_2]"
            ".FORWARD_SIM_FUNCTION[Forward_Simulation]"
        )
        numrays = 10
        items = ["RayDataX", "RayDataY", "RayDataWavelength"]
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
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[SweptEntity_10]"
            ".SWEPT_PRIMITIVE[SweptPrimitive_5]"
        )
        numpoints = int(lt.DbGet(sptkey, "NumPoints"))
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
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Cylinder_6]"
            ".CYLINDER_PRIMITIVE[CylinderPrimitive_1]"
            ".CYLINDER_SURFACE[CylinderSurface]"
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
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Lens_11]"
            ".CIRC_LENS_PRIMITIVE[LP_2]"
            ".SPLINEPATCH_LENS_SURFACE[LensRearSurface]"
        )

        u = int(lt.DbGet(srfkey, "NumPointsInU"))
        v = int(lt.DbGet(srfkey, "NumPointsInV"))

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
            "LENS_MANAGER[1].COMPONENTS[Components].SOLID[Lens_12]"
            ".CIRC_LENS_PRIMITIVE[LP_3]"
            ".SPLINESWEEP_LENS_SURFACE[LensRearSurface]"
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
        assert lt.ViewGet(key, "Title") == "Console"

    def test_3D_design_view(self, lt):
        key = lt.ViewKey("VIEW[1]")
        assert key.startswith("@")
        assert isinstance(lt.ViewKeyDump(key), str)
        assert lt.ViewGet(key, "UCSDisplayStyle") == "OpenArrowHead"
        lt.ViewSet(key, "UCSDisplayStyle", "Planes")
        assert lt.ViewGet(key, "UCSDisplayStyle") == "Planes"
