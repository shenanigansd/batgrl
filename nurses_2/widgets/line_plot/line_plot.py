import numpy as np

from ...colors import Color
from ...io import MouseEvent, MouseEventType
from ..text_widget import TextWidget, SizeHint, Anchor, Size
from ..scroll_view import ScrollView
from ._legend import _Legend
from ._traces import _Traces, TICK_WIDTH, TICK_HALF

PLOT_SIZES = [SizeHint(x, x) for x in (1.0, 1.25, 1.75, 2.75, 5.0)]


class LinePlot(TextWidget):
    """
    A 2D line plot widget.

    Parameters
    ----------
    *points : list[float] | np.ndarray
        For a single plot `points` will be `xs, ys` where xs and ys
        are each a list of floats or a 1-dimensional numpy array.
        For multiple plots, include additional xs and ys so that
        points will be `xs_0, ys_0, xs_1, ys_1, ...`.
    xmin : float | None, default: None
        Minimum x-value of plot. If None, xmin will be minimum of all xs.
    xmax : float | None, default: None
        Maximum x-value of plot. If None, xmax will be maximum of all xs.
    ymin : float | None, default: None
        Minimum y-value of plot. If None, ymin will be minimum of all ys.
    ymax : float | None, default: None
        Maximum y-value of plot. If None, ymax will be maximum of all ys.
    xlabel : str | None, default: None
        Optional label for x-axis.
    ylabel : str | None, default: None
        Optional label for y-axis.
    legend_labels : list[str] | None, default: None
        If provided, a moveable legend will be added for each plot.
    line_colors : list[Color] | None, default: None
        The color of each line plot. A rainbow gradient is used as default.
    """
    def __init__(
        self,
        *points: list[float] | np.ndarray,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        xlabel: str | None=None,
        ylabel: str | None=None,
        legend_labels: list[str] | None=None,
        line_colors: list[Color] | None=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        child_kwargs = dict(
            is_transparent=self.is_transparent,
            is_visible=self.is_visible,
            is_enabled=self.is_enabled,
            default_char=self.default_char,
            default_color_pair=self.default_color_pair,
        )

        self._trace_size_hint = 0

        self._plot = TextWidget(**child_kwargs)

        self._traces = _Traces(
            *points,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            line_colors=line_colors,
            **child_kwargs,
        )

        self._scrollview = ScrollView(
            pos=(0, TICK_WIDTH),
            show_vertical_bar=False,
            show_horizontal_bar=False,
            scrollwheel_enabled=False,
            **child_kwargs,
        )
        self._scrollview.add_widget(self._traces)

        self._tick_corner = TextWidget(
            size=(2, TICK_WIDTH),
            pos_hint=(1.0, None),
            anchor=Anchor.BOTTOM_LEFT,
            **child_kwargs,
        )
        self._tick_corner.canvas[0, -1] = "└"

        self._plot.add_widgets(
            self._scrollview,
            self._traces.x_ticks,
            self._traces.y_ticks,
            self._tick_corner,
        )

        self.add_widget(self._plot)

        if xlabel is not None:
            self.xlabel = TextWidget(size=(1, len(xlabel)), **child_kwargs)
            self.xlabel.add_text(xlabel)
            self.add_widget(self.xlabel)
        else:
            self.xlabel = None

        if ylabel is not None:
            self.ylabel = TextWidget(size=(len(ylabel), 1), **child_kwargs)
            self.ylabel.get_view[:, 0].add_text(ylabel)
            self._plot.left += 1
            self.add_widget(self.ylabel)
        else:
            self.ylabel = None

        if legend_labels is not None:
            self.legend = _Legend(
                legend_labels,
                self._traces.line_colors,
                **child_kwargs,
            )
            self.add_widget(self.legend)
        else:
            self.legend = None

    def resize(self, size: Size):
        super().resize(size)

        h, w = size

        xlabel = self.xlabel
        ylabel = self.ylabel

        has_xlabel = bool(xlabel)
        has_ylabel = bool(ylabel)

        self._plot.resize(
            (
                max(1, h - has_ylabel),
                max(1, w - has_xlabel),
            )
        )
        self._scrollview.resize(
            (
                max(1, h - 2 - has_ylabel),
                max(1, w - TICK_WIDTH - has_xlabel),
            )
        )

        hint_y, hint_x = PLOT_SIZES[self._trace_size_hint]
        self._traces.resize(
            (
                max(1, round(h * hint_y) - 2 - has_ylabel),
                max(1, round(w * hint_x) - TICK_WIDTH - has_xlabel),
            )
        )

        xlabel.pos = h - 1, (w - TICK_WIDTH - has_ylabel) // 2 - xlabel.width // 2 + TICK_WIDTH + has_ylabel
        ylabel.top = (h - 2 - has_xlabel) // 2 - ylabel.height // 2

        if self.legend:
            legend = self.legend
            legend.top = h - legend.height - 3
            legend.left = w - legend.width - TICK_HALF - TICK_WIDTH % 2

    def on_click(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        match mouse_event.event_type:
            case MouseEventType.SCROLL_UP:
                self._trace_size_hint = min(self._trace_size_hint + 1, len(PLOT_SIZES) - 1)
            case MouseEventType.SCROLL_DOWN:
                self._trace_size_hint = max(0, self._trace_size_hint - 1)
            case _:
                return super().on_click(mouse_event)

        self._traces.size_hint = PLOT_SIZES[self._trace_size_hint]
        return True
