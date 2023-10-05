"""
A text animation widget.
"""
import asyncio
from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

from ..colors import WHITE_ON_BLACK, ColorPair
from .animation import _check_frame_durations
from .text_widget import Char, TextWidget
from .widget import (
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    Widget,
)

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "TextAnimation",
]


class TextAnimation(Widget):
    """
    A text animation widget.

    Parameters
    ----------
    frames : Iterable[str] | None, default: None
        Frames of the animation.
    frame_durations : float | int | Sequence[float| int], default: 1/12
        Time each frame is displayed. If a sequence is provided, it's length
        should be equal to number of frames.
    animation_color_pair : ColorPair, default: WHITE_ON_BLACK
        Color pair of animation.
    loop : bool, default: True
        If true, restart animation after last frame.
    reverse : bool, default: False
        If true, play animation in reverse.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    frames : list[TextWidget]
        Frames of the animation.
    frame_durations : list[int | float]
        Time each frame is displayed.
    animation_color_pair : ColorPair
        Color pair of animation.
    loop : bool
        If true, animation is restarted after last frame.
    reverse : bool
        If true, animation is played in reverse.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    play:
        Play the animation. Returns a task.
    pause:
        Pause the animation
    stop:
        Stop the animation and reset current frame.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
    """

    def __init__(
        self,
        *,
        frames: Iterable[str] | None = None,
        frame_durations: float | Sequence[float] = 1 / 12,
        animation_color_pair: ColorPair = WHITE_ON_BLACK,
        loop: bool = True,
        reverse: bool = False,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self.frames = []
        if frames is not None:
            for frame in frames:
                self.frames.append(TextWidget())
                self.frames[-1].set_text(frame)
                self.frames[-1].parent = self

        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.frame_durations = _check_frame_durations(self.frames, frame_durations)
        self.animation_color_pair = animation_color_pair
        self.loop = loop
        self.reverse = reverse
        self._i = len(self.frames) - 1 if self.reverse else 0
        self._animation_task = None

    @property
    def region(self) -> Region:
        return self._region

    @region.setter
    def region(self, region: Region):
        self._region = region
        for frame in self.frames:
            frame.region = region & Region.from_rect(self.absolute_pos, frame.size)

    @property
    def animation_color_pair(self) -> ColorPair:
        return self._animation_color_pair

    @animation_color_pair.setter
    def animation_color_pair(self, animation_color_pair: ColorPair):
        self._animation_color_pair = animation_color_pair
        for frame in self.frames:
            frame.colors[:] = animation_color_pair

    @property
    def is_transparent(self) -> bool:
        """
        If true, background color and whitespace in text animation won't be painted.
        """
        return self._is_transparent

    @is_transparent.setter
    def is_transparent(self, transparent: bool):
        self._is_transparent = transparent
        for frame in self.frames:
            frame.is_transparent = transparent

    def on_remove(self):
        self.pause()
        super().on_remove()

    async def _play_animation(self):
        while self.frames:
            await asyncio.sleep(self.frame_durations[self._i])

            if self.reverse:
                self._i -= 1
                if self._i < 0:
                    self._i = len(self.frames) - 1

                    if not self.loop:
                        return
            else:
                self._i += 1
                if self._i == len(self.frames):
                    self._i = 0

                    if not self.loop:
                        return

    def play(self) -> asyncio.Task:
        """
        Play animation.
        """
        self.pause()

        if self._i == 0 and self.reverse:
            self._i = len(self.frames) - 1
        elif self._i == len(self.frames) - 1 and not self.reverse:
            self._i = 0

        self._animation_task = asyncio.create_task(self._play_animation())
        return self._animation_task

    def pause(self):
        """
        Pause animation.
        """
        if self._animation_task is not None:
            self._animation_task.cancel()

    def stop(self):
        """
        Stop the animation and reset current frame.
        """
        self.pause()
        self._i = len(self.frames) - 1 if self.reverse else 0

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        if self.frames:
            self.frames[self._i].render(canvas, colors)
        else:
            super().render(canvas, colors)
