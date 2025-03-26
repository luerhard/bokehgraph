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

# Full documentation

I am going to write a better documentation (at some point).
Please open issues if you do not understand the instructions.

Find documentation [here](https://luerhard.github.io/bokehgraph)
