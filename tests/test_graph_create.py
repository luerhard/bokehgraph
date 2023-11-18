import networkx as nx
import pytest
from bokeh.io import export_png

from bokehgraph import BokehGraph


@pytest.mark.parametrize("hover_nodes", [True, False])
@pytest.mark.parametrize("hover_edges", [True, False])
def test_barbell_plot_png(hover_nodes, hover_edges, tmp_path, image_regression):
    graph = nx.barbell_graph(5, 6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(
        graph,
        width=200,
        height=200,
        inline=False,
        hover_nodes=hover_nodes,
        hover_edges=hover_edges,
    )
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.render(
        color_by="degree",
        palette="Category20",
        max_colors=2,
        node_size=18,
    )

    test_img = tmp_path / "test_img.png"
    # for this to work, geckodriver or chromedriver have to be installed since
    # selenium is used for png export by bokeh
    export_png(figure, filename=test_img)

    with open(test_img, "rb") as f:
        img = f.read()
        image_regression.check(img)
