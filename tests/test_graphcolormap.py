import pytest

from bokehgraph.colormap import BokehGraphColorMap
from bokehgraph.colormap import BokehGraphColorMapBipartite
from bokehgraph.colormap import BokehGraphColorMapError


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
    with pytest.raises(BokehGraphColorMapError):
        BokehGraphColorMap("viridis", max_colors=257)


def test_inferno256_with_35_colors_all_palettes():
    colormap = BokehGraphColorMap("Inferno", max_colors=35)
    palette = colormap.create_palette()
    assert len(palette) == 35


def test_inferno256_with_35_colors_lowercase_palettes():
    colormap = BokehGraphColorMap("inferno", max_colors=35)
    palette = colormap.create_palette()
    assert len(palette) == 35


def test_numeric():
    colormap = BokehGraphColorMap("numeric", max_colors=257)
    palette = colormap.create_palette()
    assert len(palette) == 257


def test_map_bipartite():
    exp = ["#1f77b4", "#1f77b4", "#ff7f0e", "#440154", "#440154"]
    colormap = BokehGraphColorMapBipartite(
        palette=("Category20", "viridis"),
        n=2,
        max_colors=(2, 2),
        is_attr=(True, True),
    )
    values = [(0, 1), (0, 1), (0, 2), (1, 1), (1, 1)]
    result = colormap.map(values)

    assert result == exp
