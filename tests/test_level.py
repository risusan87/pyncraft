
from core.level import RegionFile

def test_region():
    region_file = RegionFile(0, 0)
    region = region_file.read(0, 0)
    assert region is not None
    assert region.x == 0
    assert region.z == 0