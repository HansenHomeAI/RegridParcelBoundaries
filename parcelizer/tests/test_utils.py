from pathlib import Path
from parcelizer import utils

class FakeGeom:
    def __init__(self):
        self.exterior = self
        self._coords = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]

    @property
    def coords(self):
        return self._coords


def test_save_geojson_and_vertices(tmp_path: Path, monkeypatch):
    utils.OUTPUT_DIR = tmp_path
    monkeypatch.setattr(utils, "_mapping", lambda g: {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]})
    geom = FakeGeom()
    geo_path = utils.save_geojson("x", geom)
    csv_path = utils.save_vertices("x", geom)
    assert geo_path.exists()
    assert csv_path.exists()
    data = geo_path.read_text()
    assert "Feature" in data
    lines = csv_path.read_text().splitlines()
    assert lines[0] == "lat,lon"
