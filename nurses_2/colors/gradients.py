"""
Functions for creating color gradients.
"""
import numpy as np

from .color_data_structures import *
from .colors import BLACK, WHITE, color_pair

__all__ = (
    "rainbow_gradient",
    "foreground_rainbow",
    "background_rainbow",
    "gradient",
)

def rainbow_gradient(n):
    """
    Return a rainbow gradient of `n` `Color`s.
    """
    TAU = 2 * np.pi
    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])
    THETA = TAU / n

    for i in range(n):
        yield Color(
            *(np.sin(THETA * i + OFFSETS) * 127 + 128).astype(np.uint8)
        )

def foreground_rainbow(ncolors=20, background_color: Color=BLACK):
    """
    A rainbow gradient of `ncolors` `ColorPair`s with a given background color.
    """
    return [
        color_pair(foreground_color, background_color)
        for foreground_color in rainbow_gradient(ncolors)
    ]

def background_rainbow(ncolors=20, foreground_color: Color=WHITE):
    """
    Return a rainbow gradient of `ncolors` `ColorPair`s with a given foreground color.
    """
    return [
        color_pair(foreground_color, background_color)
        for background_color in rainbow_gradient(ncolors)
    ]

def lerp(start_pair: ColorPair, end_pair: ColorPair, proportion):
    """
    Linear interpolation between `start_pair` and `end_pair`.
    """
    for a, b in zip(start_pair, end_pair):
        yield round((1 - proportion) * a + proportion * b)

def gradient(ncolors, start_pair: ColorPair, end_pair: ColorPair):
    """
    Return a gradient of `ColorPair`s from `start_pair` to `end_pair`
    with `ncolors` (> 1) colors.
    """
    assert ncolors > 1, f"not enough colors ({ncolors=})"

    grad = [ start_pair ]

    for i in range(ncolors - 2):
        proportion = (i + 1) / (ncolors - 1)
        grad.append(
            ColorPair(*lerp(start_pair, end_pair, proportion))
        )

    grad.append(end_pair)

    return grad
