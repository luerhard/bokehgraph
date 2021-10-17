# bokeh-graph
Interactive Graph visualization for networkX Graphs

# Basic Usage
```
from bokehgraph import BokehGraph
import networkx as nx

graph = nx.karate_club_graph()

plot = BokehGraph(graph)
plot.draw()
```
