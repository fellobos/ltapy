import pytest

import lighttools.error

FILENAME = "dbaccess.lts"


def test_backward_compatibility(lt):
    solids = lt.DbList("lens_manager[1].components[components]", "solid")

    assert isinstance(solids, str)
    assert solids.startswith("@")

    numsolids = 0
    while True:
        try:
            solid = lt.ListNext(solids)
        except lighttools.error.APIError:
            break
        numsolids += 1
    assert lt.ListSize(solids) == numsolids


def test_length(lt):
    solids = lt.DbList("lens_manager[1].components[components]", "solid")
    assert len(solids) == lt.ListSize(solids)

    sw_part_solids = lt.DbList(
        "lens_manager[1].components[components]", "sw_part_solid"
    )
    assert len(sw_part_solids) == 0


def test_item_access(lt):
    solids = lt.DbList("lens_manager[1].components[components]", "solid")

    assert solids[0] == lt.ListAtPos(solids, 1)
    numsolids = lt.ListSize(solids)
    assert solids[-1] == lt.ListAtPos(solids, numsolids)
    with pytest.raises(lighttools.error.APIError):
        solids[-numsolids-1]
    with pytest.raises(lighttools.error.APIError):
        solids[numsolids]

    assert solids["Toroid_4"] == lt.ListAtPos(solids, 4)
    with pytest.raises(lighttools.error.APIError):
        solids["Toroid_xx"]

    assert solids[1:3] == [lt.ListAtPos(solids, 2), lt.ListAtPos(solids, 3)]
    assert solids[:2] == [lt.ListAtPos(solids, 1), lt.ListAtPos(solids, 2)]
    assert solids[3:] == [lt.ListAtPos(solids, 4), lt.ListAtPos(solids, 5)]
    assert solids[numsolids:] == []


def test_membership(lt):
    solids = lt.DbList("lens_manager[1].components[components]", "solid")
    assert "Toroid_4" in solids
    assert "Toroid_xx" not in solids


def test_iteration(lt):
    solids = lt.DbList("lens_manager[1].components[components]", "solid")
    for i, solid in enumerate(solids):
        assert solid == lt.ListAtPos(solids, i+1)
    assert i+1 == lt.ListSize(solids)

    sw_part_solids = lt.DbList(
        "lens_manager[1].components[components]", "sw_part_solid"
    )
    i = None
    for i, sw_part_solid in enumerate(sw_part_solids):
        assert sw_part_solid == lt.ListAtPos(i+1)
    assert i is None
