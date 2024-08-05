from pathlib import Path

from bokeh.io import export_png
import networkx as nx

from bokehgraph import BokehGraph


def main():
    graph = nx.barbell_graph(5, 6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=200, height=200, inline=False)
    plot.layout(shrink_factor=1, seed=2)
    figure = plot.render(
        color_by="degree",
        palette="Category20",
        max_colors=2,
        node_size=18,
    )

    img_path = Path(__file__).parent / "simple_plot.png"
    # for this to work, geckodriver or chromedriver have to be installed since
    # selenium is used for png export by bokeh
    export_png(figure, filename=img_path)


if __name__ == "__main__":
    main()
