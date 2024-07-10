from bokeh.io import export_png
import networkx as nx
import pytest

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
        node_color="degree",
        node_palette="Category20",
        node_size=18,
        node_alpha=0.5,
        edge_color="navy",
        edge_palette="Viridis",
        edge_size=1,
        edge_alpha=0.17,
        max_colors=2,
    )

    test_img = tmp_path / "test_img.png"
    # for this to work, geckodriver or chromedriver have to be installed since
    # selenium is used for png export by bokeh
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    options = Options()
    options.add_argument("-headless")
    with webdriver.Firefox(options=options) as driver:
        export_png(figure, webdriver=driver, filename=test_img)

    with open(test_img, "rb") as f:
        img = f.read()
        image_regression.check(img, diff_threshold=1)


@pytest.mark.parametrize(
    "edges",
    [
        ((1, 2, {"weight": 1}), (2, 3, {"weight": 5}), (3, 1, {"weight": 10})),
        ((1, 2, {"weight": 10}), (2, 3, {"weight": 5}), (3, 1, {"weight": 1})),
        ((1, 2, {"weight": 5}), (2, 3, {"weight": 50}), (3, 1, {"weight": 1})),
        (
            (1, 2, {"weight": 5}),
            (2, 3, {"weight": 50}),
            (3, 1, {"weight": 1}),
            (4, 1, {"weight": 7}),
        ),
    ],
)
def test_edge_alpha_ordering(edges):
    graph = nx.Graph()

    for u, v, attrs in edges:
        graph.add_edge(u, v, **attrs)

    plot = BokehGraph(graph, hover_edges=True)

    figure = plot.render(
        node_size="age",
        node_palette="viridis",
        node_alpha=0.9,
        node_color="age",
        edge_size=15,
        edge_color="navy",
        max_colors=256,
        edge_palette="numeric",
        edge_alpha="weight",
    )
    edge_data = figure.renderers[0].data_source.data
    sorted_weights = sorted(edge_data["weight"])
    sorted_alphas = sorted(edge_data["_edge_alpha"])
    rank_weights = [sorted_weights.index(i) for i in edge_data["weight"]]
    rank_alphas = [sorted_alphas.index(i) for i in edge_data["_edge_alpha"]]

    assert rank_weights == rank_alphas

def test_graph_without_edges():
    graph = nx.Graph()
    graph.add_node(1)
    graph.add_node(2)

    plot = BokehGraph(graph, hover_edges=True)
    figure = plot.render(
        node_size="age",
        node_palette="viridis",
        node_alpha=0.9,
        node_color="age",
        edge_size=15,
        edge_color="navy",
        max_colors=256,
        edge_palette="numeric",
        edge_alpha="weight",
    )
    edge_data = figure.renderers[0].data_source.data
    node_data = figure.renderers[1].data_source.data
    assert len(edge_data["xs"]) == 0
    assert len(node_data["xs"]) == 2
