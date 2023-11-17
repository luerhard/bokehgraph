import networkx as nx
from bokehgraph import BokehGraph

def test_simple_graph_example():
    graph = nx.complete_graph(n = 3)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=400, height=300, inline=False)
    plot.layout(shrink_factor = 1)
    _= plot.draw(palette="Category20", max_colors=2, node_size=18)

    assert True