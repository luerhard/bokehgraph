from importlib.metadata import version

from .bokehgraph import BokehBipartiteGraph
from .bokehgraph import BokehGraph

__version__ = version(__name__)

__all__ = ["BokehGraph", "BokehBipartiteGraph"]
