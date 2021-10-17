# bokeh-graph
Interactive Graph visualization for networkX Graphs

# Basic Usage
```python
from bokehgraph import BokehGraph
import networkx as nx

graph = nx.karate_club_graph()

plot = BokehGraph(graph)
plot.draw()
```

## Jupyter Notebooks
To show graphs inlined in Jupyter Notebooks set the `inline` parameter
```python
plot = BokehGraph(graph, width=300, height=300, inline=True)
```

## Draw parameters

The `BokehGraph.draw()` method has a couple of parameters to individualize the resulting plot:
```
node_color="firebrick"
Set node color to any valid bokeh color (only respected if color_by is not set)

palette=None
Set palette to any valid bokeh color palette.
A list of palettes can be found under: https://docs.bokeh.org/en/latest/docs/reference/palettes.html

color_by=None
Set to a node attribute to color nodes by this attribute

edge_color="navy"
Set node color to any valid bokeh color

edge_alpha=0.17
Set edge alpha to a value between [0,1]

node_alpha=0.7
Set edge alpha to a value between [0,1]

node_size=9
Set node size

max_colors=-1
Set a maximum number of colors for color_by (or -1 to use as many colors as possible).
This must be < 256 and lower than the maximum number of colors of your selected palette.
It will divide the attribute space into evenly spaced to colors.
```