"""
Commonly used colors.
"""
from .color_data_structures import *

WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE= Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)

def color_pair(foreground: Color, background: Color) -> ColorPair:
    """
    Return a `ColorPair` from two `Color`s.
    """
    return ColorPair(*foreground, *background)

WHITE_ON_BLACK = color_pair(WHITE, BLACK)
BLACK_ON_BLACK = color_pair(BLACK, BLACK)
