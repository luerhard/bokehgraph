from bokehgraph.colormap import BokehGraphColorMap


def test_simple_two_color():
    colormap = BokehGraphColorMap("viridis", max_colors=2)
    palette = colormap.create_palette()
    assert len(palette) == 2


def test_simple_multicolor():
    colormap = BokehGraphColorMap("viridis", max_colors=24)
    palette = colormap.create_palette()
    assert len(palette) == 24
