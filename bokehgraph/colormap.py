import random
import textwrap

import bokeh
from bokeh.colors import RGB
import bokeh.palettes


class BokehGraphColorMapError(Exception):  # noqa: D101
    hint = textwrap.dedent(
        """
        Ensure color_by and palette are set to valid attributes.

        Available palettes with up to 256 colors, are:
        ["cividis", "grey", "gray", "inferno", "magma", "viridis",
        "Greys256", "Inferno256", "Magma256", "Plasma256", "Viridis256",
        "Cividis256", "Turbo256"]
        All avalailabe palettes can be found here:
        https://docs.bokeh.org/en/latest/docs/reference/palettes.html

        For attributes with more than 256 categories, a colormap can be
        computed with BokehGraph.colormap(palette, color_by, steps)
        Maximum number of steps is 256.
        Or set palette to 'random'.
    """,
    )

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):  # noqa: D105
        return self.msg + "\n" + self.hint


class BokehGraphColorMap:
    """A colormap that manages the color palette for a given attribute."""

    def __init__(self, palette, max_colors=-1):
        self.palette_name = palette

        if max_colors > 256 and self.palette_name != "numeric":
            msg = "Max number of colors is 256 !"
            raise BokehGraphColorMapError(msg)
        self.max_colors = max_colors
        self.anchors = None

    @staticmethod
    def _float_range(start, stop, step):
        while start < stop:
            yield start
            start += step

    @staticmethod
    def _color_map(categories, palette):
        return dict(zip(sorted(categories), palette))

    @staticmethod
    def _map_dict_to_iterable(d, iterable):
        return [d[i] for i in iterable]

    def _reduce_categories(self, iterable, steps):
        min_val = min(iterable)
        max_val = max(iterable)
        step_size = (max_val - min_val) / steps
        self.anchors = list(self._float_range(min_val, max_val, step_size))
        new = []
        for val in iterable:
            best = min(self.anchors, key=lambda x: abs(x - val))
            new.append(best)
        return new

    def create_palette(self):
        """Returns the palette.

        Raises:
            BokehGraphColorMapError: Raised if something went wrong.

        Returns:
            list: A list of bokeh colors.
        """
        if self.palette_name.endswith("256"):
            palette = bokeh.palettes.all_palettes[self.palette_name]
        elif self.palette_name == "numeric":
            palette = []
            i = 0
            step = 1 / self.max_colors
            for _ in range(self.max_colors):
                i += step
                palette.append(i)
        elif self.palette_name == "random":
            palette = [
                RGB(
                    random.randrange(0, 256),
                    random.randrange(0, 256),
                    random.randrange(0, 256),
                )
                for _ in range(self.max_colors)
            ]
        elif self.palette_name in [
            "cividis",
            "grey",
            "gray",
            "inferno",
            "magma",
            "viridis",
        ]:
            palette = getattr(
                bokeh.palettes,
                self.palette_name,
            )(self.max_colors)
        else:
            try:
                if 1 <= self.max_colors <= 2:
                    # Use maximum contrast if only two colors
                    palette = bokeh.palettes.all_palettes[self.palette_name][3]
                    palette = [palette[0], palette[-1]]
                else:
                    palette = bokeh.palettes.all_palettes[self.palette_name][
                        self.max_colors
                    ]
            except KeyError as e:
                msg = (
                    f"Palette {self.palette_name} does not exist or support "
                    f"{self.max_colors} colors !"
                )
                raise BokehGraphColorMapError(
                    msg,
                ) from e
        return palette

    def map(self, color_attribute):
        """Maps a color attribute.

        Args:
            color_attribute (Hashable): The attribute that should be mapped.

        Raises:
            BokehGraphColorMapError: Raised if something went wrong.

        Returns:
            Iterable: The mapped attribute.
        """
        categories = set(color_attribute)
        n_categories = len(categories)

        if self.max_colors > 0:
            if n_categories > self.max_colors:
                color_map_values = self._reduce_categories(
                    color_attribute,
                    self.max_colors,
                )
                self.max_colors = len(set(color_map_values))
            else:
                self.max_colors = n_categories
                color_map_values = color_attribute
        elif n_categories < 257 or self.palette_name == "numeric":
            self.max_colors = n_categories
            color_map_values = color_attribute
        else:
            msg = (
                f"Too many categories color attribute! {n_categories}\n"
                "Set max_colors to a value: "
                "0 < max_colors <= 256 !"
            )
            raise BokehGraphColorMapError(
                (msg),
            )
        palette = self.create_palette()
        colormap = self._color_map(set(color_map_values), palette)
        return self._map_dict_to_iterable(colormap, color_map_values)
