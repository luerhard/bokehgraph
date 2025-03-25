from __future__ import annotations

from collections import abc
from dataclasses import dataclass
from functools import lru_cache
from math import sqrt
from typing import Iterable
import warnings

import bokeh.io
from bokeh.models import HoverTool
from bokeh.models import MultiLine
from bokeh.models import Scatter
import bokeh.plotting
import networkx as nx

from .colormap import BokehGraphColorMap


@dataclass
class ParamDict:
    _node_marker: str | Iterable[str]
    _node_size: int | Iterable[int]
    _node_color: str | Iterable[str]
    _node_alpha: int | Iterable[int]
    _node_palette: str | Iterable[str]
    _edge_size: int | Iterable[int]
    _edge_color: str | Iterable[str]
    _edge_alpha: int | Iterable[int]
    _edge_palette: str | Iterable[str]
    _max_colors: int | Iterable[int]

    def __getattr__(self, name):
        _attr = getattr(self, f"_{name}")
        if isinstance(_attr, abc.Iterable) and not isinstance(_attr, str):
            return _attr
        return (_attr, _attr)


class BokehGraph:
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
        hover_nodes=False,
        hover_edges=True,
        bipartite=False,
        _testing=False,
    ):
        self.graph = graph

        self.width = width
        self.height = height

        self.hover_nodes = hover_nodes
        self.hover_edges = hover_edges

        self.bipartite = bipartite

        self._layout = None

        # inline for jupyter notebooks
        if inline:
            bokeh.io.output_notebook(hide_banner=True)
            self.show = lambda x: bokeh.plotting.show(x, notebook_handle=True)
        else:
            self.show = lambda x: bokeh.plotting.show(x)

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

    @staticmethod
    @lru_cache(maxsize=1)
    def _edge_attrs(graph):
        return {attr for _, _, data in graph.edges(data=True) for attr in data}

    def _edge_tooltips(self, graph):
        edge_tooltips = [("_type", "edge"), ("_u", "@_u"), ("_v", "@_v")]
        for attr in self._edge_attrs(graph):
            edge_tooltips.append((attr, f"@{attr}"))
        return edge_tooltips

    @staticmethod
    @lru_cache(maxsize=3)
    def _node_attrs(graph):
        return {attr for _, data in graph.nodes(data=True) for attr in data}

    def _node_tooltips(self, graph):
        node_tooltips = [("_type", "node"), ("index", "@index")]
        for attr in self._node_attrs(graph):
            if attr != "bipartite":
                node_tooltips.append((attr, f"@{attr}"))
        return node_tooltips

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

    def _render_nodes(
        self,
        figure,
        graph,
        marker,
        alpha,
        size,
        color,
        palette,
        max_colors,
    ):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Node keys in 'layout_function' don't match node keys.*",
                category=UserWarning,
            )
            graph_renderer = bokeh.plotting.from_networkx(graph, self._layout)

        if color in self._node_attrs(graph):
            colormap = BokehGraphColorMap(palette, max_colors)
            cmap = colormap.map(
                nx.get_node_attributes(graph, color, default=color).values(),
            )
            graph_renderer.node_renderer.data_source.data["_colormap"] = cmap
            color = "_colormap"

        graph_renderer.node_renderer.glyph = Scatter(
            marker=marker,
            fill_color=color,
            line_color=color,
            line_alpha=alpha,
            fill_alpha=alpha,
            size=size,
        )
        graph_renderer.edge_renderer.glyph.line_alpha = 0

        if self.hover_nodes:
            tooltips = self._node_tooltips(graph)
            formatter = {tip: "printf" for tip, _ in tooltips}
            hovertool = HoverTool(
                tooltips=tooltips,
                formatters=formatter,
                renderers=[graph_renderer.node_renderer],
                line_policy="interp",
            )
            figure.add_tools(hovertool)

        figure.renderers.append(graph_renderer)
        return figure

    def _render_edges(
        self,
        figure,
        graph,
        color,
        palette,
        size,
        alpha,
        max_colors,
    ):
        graph_renderer = bokeh.plotting.from_networkx(graph, self._layout)

        if color in self._edge_attrs(graph):
            colormap = BokehGraphColorMap(palette, max_colors)
            cmap = colormap.map(
                nx.get_edge_attributes(self.graph, color, default=color).values(),
            )
            graph_renderer.edge_renderer.data_source.data["_edge_color"] = cmap
            color = "_edge_color"

        if alpha in self._edge_attrs(graph):
            colormap = BokehGraphColorMap("numeric", max_colors)
            cmap = colormap.map(
                nx.get_edge_attributes(self.graph, alpha, default=alpha).values(),
            )
            graph_renderer.edge_renderer.data_source.data["_edge_alpha"] = cmap
            alpha = "_edge_alpha"

        if size in self._edge_attrs(graph):
            colormap = BokehGraphColorMap("numeric", max_colors)
            graph_renderer.edge_renderer.data_source.data["_edge_size"] = colormap.map(
                nx.get_edge_attributes(self.graph, size, default=size).values(),
            )
            size = "_edge_size"

        graph_renderer.edge_renderer.glyph = MultiLine(
            line_color=color,
            line_alpha=alpha,
            line_width=size,
        )
        graph_renderer.node_renderer.glyph.line_alpha = 0
        graph_renderer.node_renderer.glyph.fill_alpha = 0

        if self.hover_edges:
            tooltips = self._edge_tooltips(self.graph)
            formatter = {tip: "printf" for tip, _ in tooltips}
            us, vs = zip(*self.graph.edges())
            graph_renderer.edge_renderer.data_source.data["_u"] = us
            graph_renderer.edge_renderer.data_source.data["_v"] = vs
            hovertool = HoverTool(
                tooltips=tooltips,
                formatters=formatter,
                renderers=[graph_renderer.edge_renderer],
                line_policy="interp",
            )
            figure.add_tools(hovertool)

        figure.renderers.append(graph_renderer)
        return figure

    def draw(
        self,
        node_marker="circle",
        node_size=9,
        node_color="firebrick",
        node_alpha=0.9,
        node_palette="Category20",
        edge_size=1,
        edge_color="navy",
        edge_alpha=0.6,
        edge_palette="viridis",
        max_colors=-1,
        return_figure=False,
    ):
        params = ParamDict(
            _node_marker=node_marker,
            _node_size=node_size,
            _node_color=node_color,
            _node_alpha=node_alpha,
            _node_palette=node_palette,
            _edge_size=edge_size,
            _edge_color=edge_color,
            _edge_palette=edge_palette,
            _edge_alpha=edge_alpha,
            _max_colors=max_colors,
        )

        figure = self._prepare_figure()

        if not self._layout:
            self.layout()

        if self.graph.edges:
            figure = self._render_edges(
                figure=figure,
                graph=self.graph,
                color=edge_color,
                palette=edge_palette,
                alpha=edge_alpha,
                size=edge_size,
                max_colors=max_colors,
            )

        if self.graph.nodes:
            if not self.bipartite:
                figure = self._render_nodes(
                    figure=figure,
                    graph=self.graph,
                    marker=params.node_marker[0],
                    alpha=params.node_alpha[0],
                    size=params.node_size[0],
                    color=params.node_color[0],
                    palette=params.node_palette[0],
                    max_colors=params.max_colors[0],
                )
            else:
                level_0_nodes = (
                    node
                    for node, data in self.graph.nodes(data=True)
                    if data["bipartite"] == 0
                )
                level_1_nodes = (
                    node
                    for node, data in self.graph.nodes(data=True)
                    if data["bipartite"] == 1
                )
                level_0_subgraph = self.graph.subgraph(level_0_nodes)
                level_1_subgraph = self.graph.subgraph(level_1_nodes)
                figure = self._render_nodes(
                    figure,
                    level_0_subgraph,
                    marker=params.node_marker[0],
                    alpha=params.node_alpha[0],
                    size=params.node_size[0],
                    color=params.node_color[0],
                    palette=params.node_palette[0],
                    max_colors=params.max_colors[0],
                )
                figure = self._render_nodes(
                    figure=figure,
                    graph=level_1_subgraph,
                    marker=params.node_marker[1],
                    alpha=params.node_alpha[1],
                    size=params.node_size[1],
                    color=params.node_color[1],
                    palette=params.node_palette[1],
                    max_colors=params.max_colors[1],
                )

        if return_figure:
            return figure
        self.show(figure)
