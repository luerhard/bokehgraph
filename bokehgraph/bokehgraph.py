from collections import namedtuple
from math import sqrt

from bokeh import models
import bokeh.io
import bokeh.plotting
import networkx as nx

from .colormap import BokehGraphColorMap


class BaseBokehGraph:
    def _gen_edge_coordinates(self):
        if not self._layout:
            self.layout()

        xs = []
        ys = []
        val = namedtuple("edges", "xs ys")

        for edge in self.graph.edges():
            from_node = self._layout[edge[0]]
            to_node = self._layout[edge[1]]
            xs.append([from_node[0], to_node[0]])
            ys.append([from_node[1], to_node[1]])

        return val(xs=xs, ys=ys)

    def _gen_node_coordinates(self):
        if not self._layout:
            self.layout()

        names, coords = zip(*self._layout.items())
        node = namedtuple("node", "name x y")

        return [node(name, x, y) for name, (x, y) in zip(names, coords)]

    def layout(self, layout=None, shrink_factor=0.8, iterations=50, scale=1, seed=None):
        """Set a networkX layout for the plot.

        Args:
            layout (networkX Layout, optional): Custom layout. Defaults to None which represents
                nx.spring_layout for non-bipartite graphs and nx.bipartite_layout for bipartite
                graphs.
            shrink_factor (float, optional): Modifies spring-layout. Defaults to 0.8.
            iterations (int, optional): Modifies spring-layout. Defaults to 50.
            scale (int, optional): Modifies spring-layout. Defaults to 1.
            seed (int, optional): Modifies spring-layout. Defaults to None.
        """
        self._nodes = None
        self._edges = None
        if not layout and not self.bipartite:
            self._layout = nx.spring_layout(
                self.graph,
                k=1 / (sqrt(self.graph.number_of_nodes() * shrink_factor)),
                iterations=iterations,
                scale=scale,
                seed=seed,
            )
        elif not layout and self.bipartite:
            self._layout = nx.bipartite_layout(
                self.graph,
                (
                    node
                    for node, data in self.graph.nodes(data=True)
                    if data["bipartite"] == 0
                ),
                align="horizontal",
            )
        else:
            self._layout = layout
        return

    def _prepare_figure(self):
        fig = bokeh.plotting.figure(
            width=self.width,
            height=self.height,
            tools=["box_zoom", "reset", "wheel_zoom", "pan"],
        )

        fig.toolbar.logo = None
        fig.axis.visible = False
        fig.xgrid.grid_line_color = None
        fig.ygrid.grid_line_color = None
        return fig

    def _render_edges(
        self,
        figure,
        edge_color,
        edge_palette,
        edge_size,
        edge_alpha,
        max_colors,
    ):
        if not self._edges:
            self._edges = self._gen_edge_coordinates()

        self.edge_properties = {
            "xs": self._edges.xs,
            "ys": self._edges.ys,
        }

        try:
            xs, ys = list(zip(*self.graph.edges()))
            self.edge_properties["_u"] = xs
            self.edge_properties["_v"] = ys
        except ValueError:
            # happens if the network has no edges
            pass

        for attr in self.edge_attributes:
            self.edge_properties[attr] = [
                data[attr] for _, _, data in self.graph.edges(data=True)
            ]

        # Set edge color; potentially based on attribute
        if edge_color in self.edge_attributes:
            colormap = BokehGraphColorMap(edge_palette, max_colors)
            self.edge_properties["_colormap"] = colormap.map(
                self.edge_properties[edge_color],
            )
            color = "_colormap"
        else:
            color = edge_color

        # Set edge size; potentially based on attribute
        if edge_alpha in self.edge_attributes:
            colormap = BokehGraphColorMap("numeric", max_colors)
            self.edge_properties["_edge_alpha"] = colormap.map(
                self.edge_properties[edge_alpha],
            )
            alpha = "_edge_alpha"
        else:
            alpha = edge_alpha

        # Draw Edges
        source_edges = bokeh.models.ColumnDataSource(self.edge_properties)

        edges = figure.multi_line(
            "xs",
            "ys",
            line_color=color,
            source=source_edges,
            alpha=alpha,
            line_width=edge_size,
        )

        if self.hover_edges:
            formatter = {tip: "printf" for tip, _ in self._edge_tooltips}
            hovertool = models.HoverTool(
                tooltips=self._edge_tooltips,
                formatters=formatter,
                renderers=[edges],
                line_policy="interp",
            )
            figure.add_tools(hovertool)

        return figure


class BokehGraph(BaseBokehGraph):
    """This is instanciated with a (one-mode) networkx graph object with BokehGraph(nx.Graph()).

    working example:
    import networkx as nx
    graph = nx.barbell_graph(5,6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=800, height=600, inline=True)
    plot.layout(shrink_factor = 0.6)
    plot.draw(node_color="degree", palette="Category20", max_colors=2)


    The plot is drawn by BokehGraph.draw(node_color="firebrick")
        - node_color, line_color can be set to every value that bokeh
          recognizes, including a bokeh.colors.RGB instance. serveral other
          parameters can be found in the .draw method.


    """

    def __init__(
        self,
        graph,
        width=800,
        height=600,
        inline=True,
        hover_nodes=True,
        hover_edges=False,
    ):
        self.graph = graph
        self.bipartite = 0

        self.width = width
        self.height = height

        self.hover_nodes = hover_nodes
        self.hover_edges = hover_edges

        self._layout = None
        self._nodes = None
        self._edges = None

        self.node_properties = None

        self.node_attributes = sorted(
            {attr for _, data in self.graph.nodes(data=True) for attr in data},
        )
        if self.hover_nodes:
            self._node_tooltips = [("type", "node"), ("node", "@_node")]
            for attr in self.node_attributes:
                self._node_tooltips.append((attr, f"@{attr}"))

        self.edge_properties = None
        self.edge_attributes = sorted(
            {attr for _, _, data in self.graph.edges(data=True) for attr in data},
        )
        if self.hover_edges:
            self._edge_tooltips = [("type", "edge"), ("u", "@_u"), ("v", "@_v")]
            for attr in self.edge_attributes:
                self._edge_tooltips.append((attr, f"@{attr}"))

        # inline for jupyter notebooks
        if inline:
            bokeh.io.output_notebook(hide_banner=True)
            self.show = lambda x: bokeh.plotting.show(x, notebook_handle=True)
        else:
            self.show = lambda x: bokeh.plotting.show(x)

    def _render_nodes(
        self,
        figure,
        marker,
        node_alpha,
        node_size,
        node_color,
        node_palette,
        max_colors,
    ):
        if not self._nodes:
            self._nodes = self._gen_node_coordinates()

        xs = [node.x for node in self._nodes]
        ys = [node.y for node in self._nodes]
        nodes = [node.name for node in self._nodes]
        self.node_properties = {
            "xs": xs,
            "ys": ys,
            "_node": nodes,
        }

        nodes = self.graph.nodes

        # Color the nodes
        for attr in self.node_attributes:
            if not self.hover_nodes and attr != node_color:
                continue
            self.node_properties[attr] = [nodes[n][attr] for n in nodes]

        if node_color in self.node_attributes:
            colormap = BokehGraphColorMap(node_palette, max_colors)
            self.node_properties["_colormap"] = colormap.map(
                self.node_properties[node_color],
            )
            color = "_colormap"
        else:
            color = node_color

        source_nodes = bokeh.models.ColumnDataSource(self.node_properties)
        nodes = figure.scatter(
            "xs",
            "ys",
            marker=marker,
            fill_color=color,
            line_color=color,
            source=source_nodes,
            alpha=node_alpha,
            size=node_size,
        )

        if self.hover_nodes:
            formatter = {tip: "printf" for tip, _ in self._node_tooltips}
            hovertool = models.HoverTool(
                tooltips=self._node_tooltips,
                formatters=formatter,
                renderers=[nodes],
                attachment="vertical",
            )
            figure.add_tools(hovertool)

        return figure

    def render(
        self,
        node_color,
        node_palette,
        node_size,
        node_alpha,
        node_marker,
        edge_color,
        edge_palette,
        edge_size,
        edge_alpha,
        max_colors,
    ):
        """Render and return the bokeh figure object of your graph.

        Mostly used for debugging and testing purposes.

        Returns:
            bokeh.plotting.figure: The figure object.
        """
        figure = self._prepare_figure()

        figure = self._render_edges(
            figure=figure,
            edge_color=edge_color,
            edge_palette=edge_palette,
            edge_alpha=edge_alpha,
            edge_size=edge_size,
            max_colors=max_colors,
        )

        figure = self._render_nodes(
            figure=figure,
            marker=node_marker,
            node_color=node_color,
            node_palette=node_palette,
            node_size=node_size,
            node_alpha=node_alpha,
            max_colors=max_colors,
        )

        return figure

    def draw(
        self,
        node_color="firebrick",
        node_palette="Category20",
        node_size=9,
        node_alpha=0.7,
        node_marker="circle",
        edge_color="navy",
        edge_palette="viridis",
        edge_alpha=0.3,
        edge_size=1,
        max_colors=-1,
    ):
        """Main function to plot the graph.

        Args:
            node_color (str, optional): Color of nodes. Defaults to "firebrick".
            node_palette (str, optional): Color palette of nodes. Defaults to "Category20".
            node_size (int, optional): Size of nodes. Defaults to 9.
            node_alpha (float, optional): Alpha of nodes. Defaults to 0.7.
            edge_color (str, optional): Color of edges. Defaults to "navy".
            edge_palette (str, optional): Color palette of edges. Defaults to "viridis".
            edge_alpha (float, optional): Alpha of edges. Defaults to 0.3.
            edge_size (int, optional): Size of edges. Defaults to 1.
            max_colors (int, optional): Maximum number of different colors per attribute.
                Defaults to -1.
        """
        figure = self.render(
            node_color=node_color,
            node_palette=node_palette,
            node_size=node_size,
            node_alpha=node_alpha,
            node_marker=node_marker,
            edge_color=edge_color,
            edge_palette=edge_palette,
            edge_size=edge_size,
            edge_alpha=edge_alpha,
            max_colors=max_colors,
        )
        self.show(figure)


class BokehBipartiteGraph(BaseBokehGraph):
    """This is instanciated with a (one-mode) networkx graph object with BokehGraph(nx.Graph()).

    working example:
    import networkx as nx
    graph = nx.barbell_graph(5,6)
    degrees = nx.degree(graph)
    nx.set_node_attributes(graph, dict(degrees), "degree")
    plot = BokehGraph(graph, width=800, height=600, inline=True)
    plot.layout(shrink_factor = 0.6)
    plot.draw(color_by="degree", palette="Category20", max_colors=2)


    The plot is drawn by BokehGraph.draw(node_color="firebrick")
        - node_color, line_color can be set to every value that bokeh
          recognizes, including a bokeh.colors.RGB instance. serveral other
          parameters can be found in the .draw method.


    """

    def __init__(
        self,
        graph,
        width=800,
        height=600,
        inline=True,
        hover_nodes=True,
        hover_edges=False,
    ):
        self.graph = graph

        self.width = width
        self.height = height

        self.hover_nodes = hover_nodes
        self.hover_edges = hover_edges

        self._layout = None
        self._nodes = None
        self._edges = None

        self.bipartite = 1

        self.node_properties = {0: None, 1: None}
        self.node_attributes = {0: None, 1: None}
        self._node_tooltips = {0: None, 1: None}

        # lvl 0 set
        for node_level in [0, 1]:
            self.node_attributes[node_level] = sorted(
                {
                    attr
                    for _, data in self.graph.nodes(data=True)
                    if data["bipartite"] == node_level
                    for attr in data
                },
            )
            if self.hover_nodes:
                self._node_tooltips[node_level] = [
                    ("type", "node lv0"),
                    ("node", "@_node"),
                ]
                for attr in self.node_attributes[node_level]:
                    if attr == "bipartite":
                        continue
                    self._node_tooltips[node_level].append((attr, f"@{attr}"))

        self.edge_properties = None
        self.edge_attributes = sorted(
            {attr for _, _, data in self.graph.edges(data=True) for attr in data},
        )
        if self.hover_edges:
            self._edge_tooltips = [("type", "edge"), ("u", "@_u"), ("v", "@_v")]
            for attr in self.edge_attributes:
                self._edge_tooltips.append((attr, f"@{attr}"))

        # inline for jupyter notebooks
        if inline:
            bokeh.io.output_notebook(hide_banner=True)
            self.show = lambda x: bokeh.plotting.show(x, notebook_handle=True)
        else:
            self.show = lambda x: bokeh.plotting.show(x)

    def _gen_node_coordinates(self):
        if not self._layout:
            self.layout()

        names, coords = zip(*self._layout.items())
        node = namedtuple("node", "name x y")

        return [node(name, x, y) for name, (x, y) in zip(names, coords)]

    def _render_nodes(
        self,
        figure,
        marker,
        node_level,
        node_alpha,
        node_size,
        node_color,
        node_palette,
        max_colors,
    ):
        if not self._nodes:
            self._nodes = self._gen_node_coordinates()

        nodes = {
            node
            for node, data in self.graph.nodes(data=True)
            if data["bipartite"] == node_level
        }

        self.node_properties[node_level] = {"xs": [], "ys": [], "_node": []}

        for node in self._nodes:
            if node.name not in nodes:
                # nodes of the wrong level
                continue
            self.node_properties[node_level]["xs"].append(node.x)
            self.node_properties[node_level]["ys"].append(node.y)
            self.node_properties[node_level]["_node"].append(node.name)

        # Color the nodes
        for attr in self.node_attributes[node_level]:
            if not self.hover_nodes and attr != node_color:
                continue
            self.node_properties[node_level][attr] = [
                self.graph.nodes[n][attr] for n in nodes
            ]

        if node_color in self.node_attributes[node_level]:
            colormap = BokehGraphColorMap(node_palette, max_colors)
            self.node_properties[node_level]["_colormap"] = colormap.map(
                self.node_properties[node_level][node_color],
            )
            color = "_colormap"
        else:
            color = node_color

        source_nodes = bokeh.models.ColumnDataSource(self.node_properties[node_level])
        nodes = figure.scatter(
            "xs",
            "ys",
            marker=marker,
            fill_color=color,
            line_color=color,
            source=source_nodes,
            alpha=node_alpha,
            size=node_size,
        )

        if self.hover_nodes:
            formatter = {tip: "printf" for tip, _ in self._node_tooltips[node_level]}
            hovertool = models.HoverTool(
                tooltips=self._node_tooltips[node_level],
                formatters=formatter,
                renderers=[nodes],
                attachment="vertical",
            )
            figure.add_tools(hovertool)

        return figure

    def render(
        self,
        node_color_lv0,
        node_palette_lv0,
        node_size_lv0,
        node_alpha_lv0,
        node_marker_lv0,
        node_color_lv1,
        node_palette_lv1,
        node_size_lv1,
        node_alpha_lv1,
        node_marker_lv1,
        edge_color,
        edge_palette,
        edge_size,
        edge_alpha,
        max_colors,
    ):
        """Render and return the bokeh figure object of your graph.

        Mostly used for debugging and testing purposes.

        Returns:
            bokeh.plotting.figure: The figure object.
        """
        figure = self._prepare_figure()

        figure = self._render_edges(
            figure=figure,
            edge_color=edge_color,
            edge_palette=edge_palette,
            edge_alpha=edge_alpha,
            edge_size=edge_size,
            max_colors=max_colors,
        )

        figure = self._render_nodes(
            figure=figure,
            node_level=0,
            marker=node_marker_lv0,
            node_color=node_color_lv0,
            node_palette=node_palette_lv0,
            node_size=node_size_lv0,
            node_alpha=node_alpha_lv0,
            max_colors=max_colors,
        )

        figure = self._render_nodes(
            figure=figure,
            node_level=1,
            marker=node_marker_lv1,
            node_color=node_color_lv1,
            node_palette=node_palette_lv1,
            node_size=node_size_lv1,
            node_alpha=node_alpha_lv1,
            max_colors=max_colors,
        )

        return figure

    def draw(
        self,
        node_color_lv0="firebrick",
        node_palette_lv0="Category20",
        node_size_lv0=9,
        node_alpha_lv0=0.7,
        node_marker_lv0="circle",
        node_color_lv1="firebrick",
        node_palette_lv1="Category20",
        node_size_lv1=9,
        node_alpha_lv1=0.7,
        node_marker_lv1="square",
        edge_color="navy",
        edge_palette="viridis",
        edge_alpha=0.3,
        edge_size=1,
        max_colors=-1,
    ):
        """Main function to plot the graph.

        Args:
            node_color (str, optional): Color of nodes. Defaults to "firebrick".
            node_palette (str, optional): Color palette of nodes. Defaults to "Category20".
            node_size (int, optional): Size of nodes. Defaults to 9.
            node_alpha (float, optional): Alpha of nodes. Defaults to 0.7.
            edge_color (str, optional): Color of edges. Defaults to "navy".
            edge_palette (str, optional): Color palette of edges. Defaults to "viridis".
            edge_alpha (float, optional): Alpha of edges. Defaults to 0.3.
            edge_size (int, optional): Size of edges. Defaults to 1.
            max_colors (int, optional): Maximum number of different colors per attribute.
                Defaults to -1.
        """
        figure = self.render(
            node_color_lv0=node_color_lv0,
            node_palette_lv0=node_palette_lv0,
            node_size_lv0=node_size_lv0,
            node_alpha_lv0=node_alpha_lv0,
            node_marker_lv0=node_marker_lv0,
            node_color_lv1=node_color_lv1,
            node_palette_lv1=node_palette_lv1,
            node_size_lv1=node_size_lv1,
            node_alpha_lv1=node_alpha_lv1,
            node_marker_lv1=node_marker_lv1,
            edge_color=edge_color,
            edge_palette=edge_palette,
            edge_size=edge_size,
            edge_alpha=edge_alpha,
            max_colors=max_colors,
        )
        self.show(figure)
