from pathlib import Path

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
    figure = plot.draw(
        node_color="degree",
        node_palette="Category20",
        node_size=18,
        node_alpha=0.5,
        node_marker="circle",
        edge_color="navy",
        edge_palette="Viridis",
        edge_size=1,
        edge_alpha=0.17,
        node_max_colors=2,
        return_figure=True,
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

    with Path(test_img).open("rb") as f:
        img = f.read()
        image_regression.check(img, diff_threshold=0.1)


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

    figure = plot.draw(
        node_size="age",
        node_palette="viridis",
        node_alpha=0.9,
        node_color="age",
        node_marker="circle",
        edge_size=15,
        edge_color="navy",
        node_max_colors=256,
        edge_max_colors=10,
        edge_palette="numeric",
        edge_alpha="weight",
        return_figure=True,
    )
    edge_data = figure.renderers[0].edge_renderer.data_source.data
    sorted_weights = sorted(edge_data["weight"])
    sorted_alphas = sorted(edge_data["_alpha"])
    rank_weights = [sorted_weights.index(i) for i in edge_data["weight"]]
    rank_alphas = [sorted_alphas.index(i) for i in edge_data["_alpha"]]

    assert rank_weights == rank_alphas


def test_graph_without_edges():
    graph = nx.Graph()
    graph.add_node(1)
    graph.add_node(2)

    plot = BokehGraph(graph, hover_edges=True)
    figure = plot.draw(
        node_size="age",
        node_palette="viridis",
        node_alpha=0.9,
        node_color="age",
        node_marker="circle",
        edge_size=15,
        edge_color="navy",
        node_max_colors=256,
        edge_palette="numeric",
        edge_alpha="weight",
        return_figure=True,
    )
    node_data = figure.renderers[0].node_renderer.data_source.data
    assert len(node_data["index"]) == 2

    with pytest.raises(IndexError):
        # assert that there is only 1 renderer
        _ = figure.renderers[1].data_source.data


def test_bipartite_graph_without_edges():
    graph = nx.Graph()
    graph.add_node("agent", bipartite=0)
    graph.add_node("loc", bipartite=1)

    plot = BokehGraph(graph, hover_edges=True, bipartite=True)
    figure = plot.draw(
        node_size="age",
        node_palette="viridis",
        node_alpha=0.9,
        node_color="age",
        node_marker=("circle", "square"),
        node_max_colors=256,
        edge_size=15,
        edge_color="navy",
        edge_palette="numeric",
        edge_alpha="weight",
        return_figure=True,
    )

    node_data = figure.renderers[0].node_renderer.data_source.data
    assert len([node for node in node_data["bipartite"] if node == 1]) == 1
    assert len([node for node in node_data["bipartite"] if node == 0]) == 1

    with pytest.raises(IndexError):
        # make sure there are only to renderers
        _ = figure.renderers[3].data_source


def test_graph_bipartite():
    graph = nx.Graph()
    graph.add_node("loc1", bipartite=1, food="pizza")
    graph.add_node("loc2", bipartite=1, food="noodles")

    graph.add_node("agent1", bipartite=0, age=2)
    graph.add_node("agent2", bipartite=0, age=3)
    graph.add_node("agent3", bipartite=0, age=4)

    graph.add_edge("loc1", "agent1")
    graph.add_edge("loc1", "agent2")
    graph.add_edge("loc2", "agent2")
    graph.add_edge("loc2", "agent3")

    plot = BokehGraph(
        graph,
        width=200,
        height=200,
        inline=False,
        hover_nodes=True,
        hover_edges=True,
        bipartite=True,
    )
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.draw(
        node_color="firebrick",
        node_palette="Category20",
        node_size=9,
        node_alpha=0.7,
        node_marker=("circle", "square"),
        edge_color="navy",
        edge_palette="viridis",
        edge_alpha=0.3,
        edge_size=1,
        node_max_colors=-1,
        return_figure=True,
    )

    edge_data = figure.renderers[0].edge_renderer.data_source.data
    node_data = figure.renderers[0].node_renderer.data_source.data
    assert len(edge_data["start"]) == 4
    assert len([node for node in node_data["_marker"] if node == "circle"]) == 3
    assert len([node for node in node_data["_marker"] if node == "square"]) == 2


def test_graph_bipartite_not_connected():
    graph = nx.Graph()
    graph.add_node("loc1", bipartite=1, food="pizza")
    graph.add_node("loc2", bipartite=1, food="noodles")

    graph.add_node("agent1", bipartite=0, age=2)
    graph.add_node("agent2", bipartite=0, age=3)
    graph.add_node("agent3", bipartite=0, age=4)

    graph.add_edge("loc1", "agent1")
    graph.add_edge("loc1", "agent2")
    graph.add_edge("loc2", "agent3")

    plot = BokehGraph(
        graph,
        width=200,
        height=200,
        inline=False,
        hover_nodes=True,
        hover_edges=True,
        bipartite=True,
    )
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.draw(
        node_color=("age", "food"),
        node_palette=("viridis", "Category20"),
        node_size=26,
        node_alpha=0.9,
        node_marker=("circle", "square"),
        edge_color="navy",
        edge_size=10,
        edge_palette="Plasma",
        edge_alpha=0.5,
        node_max_colors=2,
        return_figure=True,
    )

    edge_data = figure.renderers[0].edge_renderer.data_source.data
    node_data = figure.renderers[0].node_renderer.data_source.data
    assert len(edge_data["start"]) == 3
    assert len([node for node in node_data["_marker"] if node == "circle"]) == 3
    assert len([node for node in node_data["_marker"] if node == "square"]) == 2


def test_removed_bipartite_attr():
    graph = nx.Graph()
    graph.add_node("loc1")
    graph.add_node("loc2")

    graph.add_node("agent1")
    graph.add_node("agent2")
    graph.add_node("agent3")

    graph.add_edge("loc1", "agent1")
    graph.add_edge("loc1", "agent2")
    graph.add_edge("loc2", "agent3")
    graph.add_edge("loc2", "loc1")

    plot = BokehGraph(
        graph,
        width=200,
        height=200,
        inline=False,
        hover_nodes=True,
        hover_edges=True,
    )
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.draw(
        node_palette="Category20",
        node_size=26,
        node_marker="circle",
        edge_size=10,
        edge_palette="Plasma",
        edge_alpha=0.5,
        node_alpha=0.9,
        node_color="firebrick",
        edge_color="navy",
        node_max_colors=2,
        return_figure=True,
    )

    edge_data = figure.renderers[0].edge_renderer.data_source.data
    node_data = figure.renderers[0].node_renderer.data_source.data
    assert len(edge_data["start"]) == 4
    assert len(node_data["index"]) == 5


def test_bipartite_node_color_single_level(tmp_path, image_regression):
    g = nx.Graph()
    g.add_node(1, bipartite=0, gender="m")
    g.add_node(2, bipartite=0, gender="w")
    g.add_node(3, bipartite=1)
    g.add_node(4, bipartite=1)
    g.add_edge(1, 3)
    g.add_edge(1, 4)
    g.add_edge(2, 3)
    g.add_edge(2, 4)

    plot = BokehGraph(
        g,
        width=500,
        height=500,
        hover_edges=True,
        bipartite=True,
        inline=False,
    )
    figure = plot.draw(
        node_color=("gender", "firebrick"),
        node_palette=("viridis", "Category20"),
        node_size=20,
        node_alpha=0.9,
        node_marker=("circle", "square"),
        edge_color="navy",
        edge_size=10,
        edge_palette="Plasma",
        edge_alpha=0.5,
        node_max_colors=2,
        return_figure=True,
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

    with Path(test_img).open("rb") as f:
        img = f.read()
        image_regression.check(img, diff_threshold=0.1)


def test_bipartite_node_color_only_one_value_in_attribute(tmp_path, image_regression):
    g = nx.Graph()
    g.add_node(1, bipartite=0, gender="m")
    g.add_node(2, bipartite=0, gender="m")
    g.add_node(3, bipartite=1, gender="m")
    g.add_node(4, bipartite=1, gender="m")
    g.add_edge(1, 3)
    g.add_edge(1, 4)
    g.add_edge(2, 3)
    g.add_edge(2, 4)

    plot = BokehGraph(
        g,
        width=500,
        height=500,
        hover_edges=True,
        inline=False,
        bipartite=True,
    )
    figure = plot.draw(
        node_color="gender",
        node_palette=("viridis", "Category20"),
        node_size=20,
        node_alpha=0.8,
        node_marker=("circle", "square"),
        edge_color="navy",
        edge_size=10,
        edge_palette="Plasma",
        edge_alpha=0.5,
        node_max_colors=2,
        return_figure=True,
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

    with Path(test_img).open("rb") as f:
        img = f.read()
        image_regression.check(img, diff_threshold=0.1)


def test_keep_property_order_world_graph():
    nodes = [
        (2, {"bipartite": 1, "type": "Location"}),
        (3, {"bipartite": 0}),
        (4, {"bipartite": 0}),
        (5, {"bipartite": 0}),
        (6, {"bipartite": 1, "type": "School"}),
        (1, {"bipartite": 0}),
        (7, {"bipartite": 1, "type": "Location"}),
        (8, {"bipartite": 1, "type": "World"}),
    ]

    edges = [
        (2, 3, {"weight": 1}),
        (3, 8, {"weight": 1}),
        (4, 6, {"weight": 1}),
        (4, 7, {"weight": 1}),
        (4, 8, {"weight": 1}),
        (5, 6, {"weight": 1}),
        (5, 8, {"weight": 1}),
        (1, 7, {"weight": 1}),
        (1, 8, {"weight": 1}),
    ]

    graph = nx.Graph()
    for node, attrs in nodes:
        graph.add_node(node, **attrs)
    for u, v, attrs in edges:
        graph.add_edge(u, v, **attrs)

    graph_layout = nx.drawing.spring_layout(graph)
    plot = BokehGraph(
        graph,
        width=400,
        height=400,
        hover_edges=True,
        bipartite=True,
        inline=False,
    )
    plot.layout(layout=graph_layout)

    figure = plot.draw(
        node_color="firebrick",
        node_palette="Category20",
        node_size=9,
        node_alpha=0.7,
        node_marker=("circle", "square"),
        edge_color="navy",
        edge_palette="viridis",
        edge_alpha=0.3,
        edge_size=1,
        node_max_colors=-1,
        return_figure=True,
    )

    exp_types = [attr["type"] for node, attr in graph.nodes(data=True) if attr["bipartite"] == 1]

    node_data = figure.renderers[0].node_renderer.data_source.data
    types = [data for data, node in zip(node_data["type"], node_data["bipartite"]) if node == 1]
    assert exp_types == types
