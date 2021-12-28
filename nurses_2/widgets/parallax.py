from typing import Sequence

import numpy as np

from .graphic_widget import GraphicWidget


class Parallax(GraphicWidget):
    """
    A parallax widget.

    Parameters
    ----------
    layers : Sequence[GraphicWidget]
        Individual layers of the parallax in background-to-foreground order.
    speeds : Sequence[float] | None, default: None
        The scrolling speed of each individual layer. A speed of x will scroll a
        layer by `round(x * offset)` where offset is either `vertical_offset` or
        `horizontal_offset` of the parallax. Default speeds are `1/(N - i)`
        where `N` is the number of layers and `i` is the index of a layer.
    """
    def __init__(self, *, layers: Sequence[GraphicWidget], speeds: Sequence[float] | None=None, **kwargs):
        super().__init__(**kwargs)

        self.layers = layers

        self._image_copies = [layer.texture.copy() for layer in layers]

        nlayers = len(layers)
        self.speeds = speeds or [1 / (nlayers - i) for i in range(nlayers)]

        self._vertical_offset = self._horizontal_offset = 0

        for widget in layers:
            self.add_widget(widget)

    def update_geometry(self):
        super().update_geometry()
        self._image_copies = [layer.texture.copy() for layer in self.layers]

    @property
    def vertical_offset(self):
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset):
        self._vertical_offset = offset
        self._adjust()

    @property
    def horizontal_offset(self):
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset):
        self._horizontal_offset = offset
        self._adjust()

    @property
    def offset(self):
        return self._vertical_offset, self._horizontal_offset

    @offset.setter
    def offset(self, offset):
        self._vertical_offset, self._horizontal_offset = offset
        self._adjust()

    def _adjust(self):
        for speed, image, layer in zip(
            self.speeds,
            self._image_copies,
            self.layers
        ):
            rolls = -round(speed * self._vertical_offset), -round(speed * self._horizontal_offset)
            axis = 0, 1
            layer.texture = np.roll(image, rolls, axis)
