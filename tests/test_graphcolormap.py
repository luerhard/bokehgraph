import pytest

from bokehgraph.colormap import BokehGraphColorMap
from bokehgraph.colormap import BokehGraphColorMapException


def test_simple_two_color():
    colormap = BokehGraphColorMap("viridis", max_colors=2)
    palette = colormap.create_palette()
    assert len(palette) == 2


def test_simple_multicolor():
    colormap = BokehGraphColorMap("viridis", max_colors=24)
    palette = colormap.create_palette()
    assert len(palette) == 24

def test_max_colors_255():
    colormap = BokehGraphColorMap("viridis", max_colors=255)
    palette = colormap.create_palette()
    assert len(palette) == 255


def test_max_colors_256():
    with pytest.raises(BokehGraphColorMapException):
        colormap = BokehGraphColorMap("viridis", max_colors=257)


def test_numeric():
    colormap = BokehGraphColorMap("numeric", max_colors=257)
    palette = colormap.create_palette()
    assert len(palette) == 257
