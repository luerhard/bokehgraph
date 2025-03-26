from __future__ import annotations

from collections import abc
from dataclasses import dataclass
from math import sqrt
from typing import Iterable

import bokeh.io
from bokeh.models import HoverTool
from bokeh.models import MultiLine
from bokeh.models import Scatter
import bokeh.plotting
import networkx as nx

from .colormap import BokehGraphColorMap
from .colormap import BokehGraphColorMapBipartite


@dataclass
class ParamDict:
    graph: nx.Graph
    _node_marker: str | Iterable[str]
    _node_size: int | Iterable[int]
    _node_color: str | Iterable[str]
    _node_palette: str | Iterable[str]
    _node_max_colors: int | Iterable[int]
    _node_alpha: float | Iterable[float]
    _edge_size: int | Iterable[int]
    _edge_color: str | Iterable[str]
    _edge_palette: str | Iterable[str]
    _edge_max_colors: int | Iterable[int]
    _edge_alpha: float | Iterable[float]

    def __post_init__(self):
        self.graph_node_attrs = {attr for _, data in self.graph.nodes(data=True) for attr in data}
        self.graph_edge_attrs = {
            attr for _, _, data in self.graph.edges(data=True) for attr in data
        }

    def __getattr__(self, name):
        _attr = getattr(self, f"_{name}")
        if name.startswith("edge") or (
            isinstance(_attr, abc.Iterable) and not isinstance(_attr, str)
        ):
            return _attr
        return (_attr, _attr)

    def is_node_attr(self, name):
        if isinstance(name, abc.Iterable) and not isinstance(name, str):
            return (name[0] in self.graph_node_attrs, name[1] in self.graph_node_attrs)
        else:
            return (name in self.graph_node_attrs,) * 2

    def is_edge_attr(self, name):
        return (name in self.graph_edge_attrs,)


class BokehGraph:
    """This is instanciated with a (one-mode) networkx graph object with BokehGraph(nx.Graph())."""

    def __init__(
        self,
        graph,
        width=600,
        height=600,
        inline=True,
        hover_nodes=True,
        hover_edges=False,
        bipartite=False,
    ):
        """Create a BokehGraph object.

        Args:
            graph (nx.Graph): The graph to be plotted.
            width (int, optional): Width of the figure. Defaults to 600.
            height (int, optional): Height of the figure. Defaults to 600.
            inline (bool, optional): If true, inlines the figure in a jupyter notebook. Creates a
                new tab in the browser to display it there instead if false.
                Defaults to True.
            hover_nodes (bool, optional): Enable hover tool for nodes. Defaults to True.
            hover_edges (bool, optional): Enable hover tool for edges. Defaults to False.
            bipartite (bool, optional): Plot graph as bipartite graph. Defaults to False.
        """
        self.graph = graph

        self.width = width
        self.height = height

        self.hover_nodes = hover_nodes
        self.hover_edges = hover_edges

        self.bipartite = bipartite

        self._layout = None

        self._levels = {data.get("bipartite") for _, data in graph.nodes(data=True)}

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
                (node for node, data in self.graph.nodes(data=True) if data["bipartite"] == 0),
                align="horizontal",
            )
        else:
            self._layout = layout
        return

    def _edge_tooltips(self, params):
        edge_tooltips = [("start", "@start"), ("end", "@end")]
        for attr in params.graph_edge_attrs:
            edge_tooltips.append((attr, f"@{attr}"))
        return edge_tooltips

    def _node_tooltips(self, params):
        node_tooltips = [("index", "@index")]
        for attr in params.graph_node_attrs:
            if attr != "bipartite":
                node_tooltips.append((attr, f"@{attr}"))
        return node_tooltips

    def tooltip_css(self, renderer, render_data):
        css = "<div><table>"
        row = """
        <td style='text-align: right;color: #4682b4;'>{name}</td>
        <td>:</td>
        <td style='text-align: left;'>{index}</td>
        """
        col = """
        <tr style='display:@{{{name}_display}};'>
        {row}
        </tr>
        """
        for render_name, tooltips in render_data:
            for name, index in tooltips:
                data = getattr(renderer, render_name).data_source.data.get(name)
                if render_name == "node_renderer":
                    render_other = "edge_renderer"
                else:
                    render_other = "node_renderer"
                getattr(renderer, render_name).data_source.data[f"{name}_display"] = [
                    "none" if val is None else 1 for val in data
                ]
                n_data = len(next(iter(getattr(renderer, render_other).data_source.data.values())))
                getattr(renderer, render_other).data_source.data[f"{name}_display"] = [
                    "none",
                ] * n_data
                css += col.format(row=row.format(name=name, index=index), name=name)
        css += "</table></div>"
        return css

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

    def _get_node_attr(self, attr):
        return [
            (
                data.get("bipartite", 0),
                data.get(attr[data.get("bipartite", 0)], attr[data.get("bipartite", 0)]),
            )
            for _, data in self.graph.nodes(data=True)
        ]

    def _get_edge_attr(self, attr):
        return nx.get_edge_attributes(self.graph, attr)

    def _map_node_attr(self, attr):
        return [attr[data.get("bipartite", 0)] for _, data in self.graph.nodes(data=True)]

    def _render_nodes(self, renderer, params):
        renderer.node_renderer.data_source.data["_marker"] = self._map_node_attr(params.node_marker)

        map_ = BokehGraphColorMapBipartite(
            palette=params.node_palette,
            n=len(self._levels),
            max_colors=params.node_max_colors,
            is_attr=params.is_node_attr(params.node_color),
        )
        node_vals = self._get_node_attr(params.node_color)
        values = map_.map(node_vals)
        renderer.node_renderer.data_source.data["_color"] = values

        map_ = BokehGraphColorMapBipartite(
            palette=("numeric", "numeric"),
            n=len(self._levels),
            max_colors=params.node_max_colors,
            is_attr=params.is_node_attr(params.node_alpha),
        )
        node_vals = self._get_node_attr(params.node_alpha)
        values = map_.map(node_vals)
        renderer.node_renderer.data_source.data["_alpha"] = values

        map_ = BokehGraphColorMapBipartite(
            palette=("numeric", "numeric"),
            n=len(self._levels),
            max_colors=params.node_max_colors,
            is_attr=params.is_node_attr(params.node_size),
        )
        node_vals = self._get_node_attr(params.node_size)
        values = map_.map(node_vals)
        renderer.node_renderer.data_source.data["_size"] = values

        renderer.node_renderer.glyph = Scatter(
            marker="_marker",
            fill_color="_color",
            line_color="_color",
            line_alpha="_alpha",
            fill_alpha="_alpha",
            size="_size",
        )

        return renderer

    def _render_edges(self, renderer, params):
        if params.is_edge_attr(params.edge_color):
            colormap = BokehGraphColorMap(params.edge_palette, params.edge_max_colors)
            values = colormap.map_iter(
                nx.get_edge_attributes(
                    self.graph,
                    params.edge_color,
                    default=params.edge_color,
                ).values(),
            )
            renderer.edge_renderer.data_source.data["_color"] = values
        else:
            renderer.edge_renderer.data_source.data["_color"] = [
                params.edge_color,
            ] * nx.number_of_edges(self.g)

        if params.is_edge_attr(params.edge_alpha):
            colormap = BokehGraphColorMap("numeric", params.edge_max_colors)
            values = colormap.map_iter(
                nx.get_edge_attributes(
                    self.graph,
                    params.edge_alpha,
                    default=params.edge_alpha,
                ).values(),
            )
            renderer.edge_renderer.data_source.data["_alpha"] = values
        else:
            renderer.edge_renderer.data_source.data["_alpha"] = [
                params.edge_alpha,
            ] * nx.number_of_edges(self.g)

        if params.is_edge_attr(params.edge_size):
            colormap = BokehGraphColorMap("numeric", params.edge_max_colors)
            values = colormap.map_iter(
                nx.get_edge_attributes(
                    self.graph,
                    params.edge_size,
                    default=params.edge_size,
                ).values(),
            )
            renderer.edge_renderer.data_source.data["_size"] = values
        else:
            renderer.edge_renderer.data_source.data["_size"] = [
                params.edge_size,
            ] * nx.number_of_edges(self.g)

        renderer.edge_renderer.glyph = MultiLine(
            line_color="_color",
            line_alpha="_alpha",
            line_width="_size",
        )

        return renderer

    def draw(
        self,
        node_marker=("circle", "square"),
        node_size=12,
        node_color=("firebrick", "steelblue"),
        node_alpha=0.9,
        node_palette="Category20",
        node_max_colors=-1,
        edge_size=2,
        edge_color="navy",
        edge_alpha=0.6,
        edge_palette="viridis",
        edge_max_colors=-1,
        return_figure=False,
    ):
        """Create the actual visualization.

        Args:
            node_marker (str | tuple[str], optional): Defines the shape of the nodes.
                A list of possible values can be found here:
                https://docs.bokeh.org/en/latest/docs/examples/basic/scatters/markers.html.
                Defaults to ("circle", "square").
            node_size (int | str | tuple[int | str], optional): Set the size of the nodes.
                If it is an integer, all nodes get that size. If it is the name of a node attribute,
                node size will be set according to this attribute.
                Defaults to 12.
            node_color (str | tuple[str], optional): Set the color of the nodes. If it is a name
                of a color or a hex value, all nodes will have that color. If it is the name of a
                node attribute, nodes will be colored according to that attribute.
                Defaults to ("firebrick", "steelblue").
            node_alpha (float | str | tuple[float | str], optional): Set the alpha value for nodes.
                If it is a float, all nodes get that value. If it is a node attribute, alpha will be
                set according to that attribute.
                Defaults to 0.9.
            node_palette (str | tuple[str], optional): Set palettes to choose node colors from. See
                Colormap for a list of possible palettes.
                Defaults to "Category20".
            node_max_colors (int | tuple[int], optional): Set the maximum number of colors to use
                for node attributes. Also applies to number of different values for node_alpha and
                node_size.
                Defaults to -1 which is to use all available colors of a palette.
            edge_size (int | str | tuple[int | str], optional): Set the width of the edges.
                If it is an integer, all edges get that width. If it is the name of a edge
                attribute, edge size will be set according to this attribute.
                Defaults to 2.
            edge_color (str | tuple[str], optional): Set the color of the edges. If it is a name
                of a color or a hex value, all edges will have that color. If it is the name of a
                edge attribute, edges will be colored according to that attribute.
                Defaults to "navy".
            edge_alpha (float | str | tuple[float | str], optional): Set the alpha value for edges.
                If it is a float, all edges get that value. If it is a edge attribute, alpha will be
                set according to that attribute.
                Defaults to 0.6.
            edge_palette (str | tuple[str], optional): Set palette to choose edge colors from. See
                Colormap for a list of possible palettes.
                Defaults to "viridis".
            edge_max_colors (int | tuple[int], optional): Set the maximum number of colors to use
                for edge attributes. Also applies to number of different values for edge_alpha and
                edge_size.
                Defaults to -1 which is to use all available colors of a palette.
            return_figure (bool, optional): Return bokeh figure object instead of displaying the
                graph. Useful if you want to save the plot or modify it further.
                Defaults to False.

        Returns:
            bokeh.plotting.figure | None: Optional return of the figure if return_figure is set.
        """
        params = ParamDict(
            graph=self.graph,
            _node_marker=node_marker,
            _node_size=node_size,
            _node_color=node_color,
            _node_palette=node_palette,
            _node_max_colors=node_max_colors,
            _node_alpha=node_alpha,
            _edge_size=edge_size,
            _edge_color=edge_color,
            _edge_palette=edge_palette,
            _edge_max_colors=edge_max_colors,
            _edge_alpha=edge_alpha,
        )

        figure = self._prepare_figure()

        if not self._layout:
            self.layout()

        renderer = bokeh.plotting.from_networkx(self.graph, self._layout)

        if self.graph.edges:
            renderer = self._render_edges(renderer=renderer, params=params)

        if self.graph.nodes:
            renderer = self._render_nodes(renderer=renderer, params=params)

        if self.hover_edges or self.hover_nodes:
            tooltips_renderers = []
            tooltips_render_data = []
            if self.hover_edges:
                tooltips = self._edge_tooltips(params)
                tooltips_render_data.append(["edge_renderer", tooltips])
                tooltips_renderers.append(renderer.edge_renderer)
            if self.hover_nodes:
                tooltips = self._node_tooltips(params)
                tooltips_render_data.append(["node_renderer", tooltips])
                tooltips_renderers.append(renderer.node_renderer)

            hovertool = HoverTool(
                tooltips=self.tooltip_css(renderer, tooltips_render_data),
                renderers=tooltips_renderers,
                line_policy="interp",
            )
            figure.add_tools(hovertool)
        figure.renderers.append(renderer)

        if return_figure:
            return figure
        self.show(figure)
