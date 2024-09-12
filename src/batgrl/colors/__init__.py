"""Color-related functions and data structures."""

from .color_types import AColor, Color, ColorPair, ColorTheme
from .colors import (
    ABLACK,
    ABLUE,
    ACYAN,
    AGREEN,
    AMAGENTA,
    ARED,
    AWHITE,
    AYELLOW,
    BLACK,
    BLUE,
    CYAN,
    DEFAULT_COLOR_THEME,
    DEFAULT_PRIMARY_BG,
    DEFAULT_PRIMARY_FG,
    GREEN,
    MAGENTA,
    RED,
    TRANSPARENT,
    WHITE,
    YELLOW,
    Neptune,
)
from .gradients import (
    darken_only,
    gradient,
    lerp_colors,
    lighten_only,
    rainbow_gradient,
)

__all__ = [
    "ABLACK",
    "ABLUE",
    "ACYAN",
    "AGREEN",
    "AMAGENTA",
    "ARED",
    "AWHITE",
    "AYELLOW",
    "BLACK",
    "BLACK_ON_BLACK",
    "BLUE",
    "CYAN",
    "DEFAULT_COLOR_THEME",
    "DEFAULT_PRIMARY_BG",
    "DEFAULT_PRIMARY_FG",
    "GREEN",
    "MAGENTA",
    "RED",
    "TRANSPARENT",
    "WHITE",
    "WHITE_ON_BLACK",
    "YELLOW",
    "AColor",
    "Color",
    "ColorPair",
    "ColorTheme",
    "Neptune",
    "darken_only",
    "gradient",
    "lerp_colors",
    "lighten_only",
    "rainbow_gradient",
]
