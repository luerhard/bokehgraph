import networkx as nx
from bokehgraph import BokehGraph


def test_simple_graph_example():
    graph = nx.barbell_graph(5, 6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=400, height=300, inline=False)
    plot.layout(shrink_factor=1, seed=2)
    _ = plot.draw(palette="Category20", max_colors=2, node_size=18)

    assert True
