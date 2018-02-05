import pytest

import ltapy.error

FILENAME = "dbaccess.lts"


def test_backward_compatibility(lt):
    solids = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")

    assert isinstance(solids, str)
    assert solids.startswith("@")

    numsolids = 0
    while True:
        try:
            lt.ListNext(solids)
        except ltapy.error.APIError:
            break
        numsolids += 1
    assert lt.ListSize(solids) == numsolids


def test_length(lt):
    solids = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")
    assert len(solids) == lt.ListSize(solids)

    sw_part_solids = lt.DbList(
        "LENS_MANAGER[1].COMPONENTS[Components]", "SW_PART_SOLID"
    )
    assert len(sw_part_solids) == 0


def test_item_access(lt):
    solids = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")

    assert solids[0] == lt.ListAtPos(solids, 1)
    numsolids = lt.ListSize(solids)
    assert solids[-1] == lt.ListAtPos(solids, numsolids)
    with pytest.raises(ltapy.error.APIError):
        solids[-numsolids-1]
    with pytest.raises(ltapy.error.APIError):
        solids[numsolids]

    assert solids["Toroid_4"] == lt.ListAtPos(solids, 4)
    with pytest.raises(ltapy.error.APIError):
        solids["Toroid_xx"]

    assert solids[1:3] == [lt.ListAtPos(solids, 2), lt.ListAtPos(solids, 3)]
    assert solids[:2] == [lt.ListAtPos(solids, 1), lt.ListAtPos(solids, 2)]
    assert solids[3:] == [lt.ListAtPos(solids, 4), lt.ListAtPos(solids, 5)]
    assert solids[numsolids:] == []


def test_membership(lt):
    solids = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")
    assert "Toroid_4" in solids
    assert "Toroid_xx" not in solids


def test_iteration(lt):
    solids = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")
    for i, solid in enumerate(solids):
        assert solid == lt.ListAtPos(solids, i+1)
    assert i+1 == lt.ListSize(solids)

    sw_part_solids = lt.DbList(
        "LENS_MANAGER[1].COMPONENTS[Components]", "SW_PART_SOLID"
    )
    i = None
    for i, sw_part_solid in enumerate(sw_part_solids):
        assert sw_part_solid == lt.ListAtPos(i+1)
    assert i is None


def test_garbage_collection(lt):
    # The DbList object must not be garbage collected if no name is
    # assigned to the list.
    cylinder = lt.DbList("LENS_MANAGER[1].COMPONENTS[Components]", "SOLID")[-1]
    assert lt.DbGet(cylinder, "Name") == "Cylinder_5"
