from pathlib import Path

import networkx as nx
import numpy as np
from bokeh.io import export_png
from PIL import Image

from bokehgraph import BokehGraph


def test_barbell_render_no_exception():
    graph = nx.barbell_graph(5, 6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=400, height=300, inline=False)
    plot.layout(shrink_factor=1, seed=2)
    _ = plot.render(color_by="degree", palette="Category20", max_colors=2, node_size=18)

    assert True


def test_edge_attributes():
    graph = nx.Graph()
    nx.add_path(graph, [1, 2, 3, 4], myattr="this_attr")
    plot = BokehGraph(graph, width=50, height=50, inline=False, hover_nodes=False, hover_edges=True)
    figure = plot.render()


def assert_images_equal(image_1: str, image_2: str):
    img1 = Image.open(image_1)
    img2 = Image.open(image_2)

    # Convert to same mode and size for comparison
    img2 = img2.convert(img1.mode)
    img2 = img2.resize(img1.size)

    sum_sq_diff = np.sum(
        (np.asarray(img1).astype("float") - np.asarray(img2).astype("float")) ** 2
    )

    if sum_sq_diff == 0:
        # Images are exactly the same
        pass
    else:
        normalized_sum_sq_diff = sum_sq_diff / np.sqrt(sum_sq_diff)
        assert normalized_sum_sq_diff < 0.001


def test_barbell_plot_png(tmp_path):
    graph = nx.barbell_graph(5, 6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=200, height=200, inline=False)
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.render(
        color_by="degree", palette="Category20", max_colors=2, node_size=18
    )

    test_img = tmp_path / "test_img.png"
    # for this to work, geckodriver or chromedriver have to be installed since
    # selenium is used for png export by bokeh
    export_png(figure, filename=test_img)

    exp_img = Path(__file__).parent / "data/simple_plot.png"

    assert_images_equal(test_img, exp_img)
