# ColorMap

This is a helper class that manages the creation of colormaps for nodes.


Ensures color_by and palette are set to valid attributes.

Available palettes with up to 256 colors, are:
["cividis", "grey", "gray", "inferno", "magma", "viridis",
"Greys", "Inferno", "Magma", "Plasma", "Viridis",
"Cividis", "Turbo"]
All avalailabe palettes can be found here:
https://docs.bokeh.org/en/latest/docs/reference/palettes.html

For attributes with more than 256 categories, a colormap can be
computed with BokehGraph.colormap(palette, color_by, steps)
Maximum number of steps is 256.
Or set palette to 'random'.

## BokehGraphColorMap

```{eval-rst}
.. autoclass:: bokehgraph.colormap.BokehGraphColorMap
    :members:
    :undoc-members:

```
