import numpy as np
from wcwidth import wcswidth

from ..colors import WHITE_ON_BLACK
from ..data_structures import Point, Size
from ..io import Key
from .widget_data_structures import CanvasView, Rect
from ..utils import character_width


class Widget:
    """
    A generic TUI element.

    Parameters
    ----------
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    is_transparent : bool, default: False
        If true, white-space is "see-through".
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of widget.
    """
    def __init__(
        self,
        size: Size=Size(10, 10),
        pos: Point=Point(0, 0),
        *,
        is_transparent=False,
        is_visible=True,
        is_enabled=True,
        default_char=" ",
        default_color_pair=WHITE_ON_BLACK,
    ):
        self._size = size
        self.pos = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

        self.parent = None
        self.children = [ ]

        self.canvas = np.full(size, default_char, dtype=object)
        self.colors = np.full((*size, 6), default_color_pair, dtype=np.uint8)

        self.default_char = default_char
        self.default_color_pair = default_color_pair

    def resize(self, size: Size):
        """
        Resize widget. Content is preserved as much as possible.
        """
        self._size = h, w = size

        old_canvas = self.canvas
        old_colors = self.colors

        old_h, old_w = old_canvas.shape

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.canvas = np.full(size, self.default_char, dtype=object)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self.canvas[:copy_h, :copy_w] = old_canvas[:copy_h, :copy_w]
        self.colors[:copy_h, :copy_w] = old_colors[:copy_h, :copy_w]

        for child in self.children:
            child.update_geometry()

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def size(self):
        return self._size

    @property
    def pos(self):
        """
        Relative position to parent.
        """
        return Point(self.top, self.left)

    @pos.setter
    def pos(self, point: Point):
        self.top, self.left = point

    @property
    def absolute_pos(self):
        """
        Absolute position on screen.
        """
        y, x = self.parent.absolute_pos
        return Point(self.top + y, self.left + x)

    @property
    def height(self):
        return self._size[0]

    @property
    def width(self):
        return self._size[1]

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def right(self):
        return self.left + self.width

    @property
    def default_fg_color(self):
        return self.default_color_pair.fg_color

    @property
    def default_bg_color(self):
        return self.default_color_pair.bg_color

    @property
    def rect(self):
        """
        `Rect` of bounding box relative to parent.

        Notes
        -----
        `rect` of root widget is same as `absolute_rect`.
        """
        return Rect(
            self.top,
            self.left,
            self.bottom,
            self.right,
            self.height,
            self.width
        )

    @property
    def absolute_rect(self):
        """
        `Rect` of bounding box on screen.
        """
        top, left = self.absolute_pos
        height, width = self.size
        return Rect(
            top,
            left,
            top + height,
            left + width,
            height,
            width,
        )

    @property
    def center(self):
        return Point(self.height // 2, self.width // 2)

    @property
    def root(self):
        """
        The root widget.
        """
        return self.parent.root

    @property
    def app(self):
        """
        The running app.
        """
        return self.root.app

    def normalize_canvas(self):
        """
        Add zero-width characters after each full-width character.

        Raises
        ------
        ValueError
            If full-width character is followed by non-default character.

        Notes
        -----
        In some cases, even with normalized canvases, widgets with full-width characters
        could cause display issues.

        Imagine the following arrangement of widgets:
                      _________
                     | fw  ____|___
                     | fw | fw  ___|__
                     | fw | fw | fw  _|__
                     | fw | fw | fw | fw |
                     |____|____|____|____|

        `fw` represents a full-width character and each widget is offset from the next by one.
        One can end up with an entire row of full-width characters which will likely ruin the
        display. If `normalize_canvas` and `add_text` aren't sufficient for the user, a custom
        render method will likely need to be implemented.
        """
        canvas = self.canvas
        default_char = self.default_char

        char_widths = character_width(self.canvas)

        canvas[char_widths == 0] = default_char  # Zero-width characters are replaced with the default character.

        where_fullwidth = np.argwhere(char_widths == 2)
        for y, x in where_fullwidth:
            if x == self.width - 1:
                raise ValueError("can't normalize, full-width character on edge")

            if canvas[y, x + 1] != default_char:
                raise ValueError("can't normalize, full-width character followed by non-default char")

            canvas[y, x + 1] = chr(0x200B)  # Zero-width space

    @property
    def get_view(self) -> CanvasView:
        """
        A wrapper around the canvas with an `add_text` method. This is to
        simplify adding text to views of the underlying canvas.

        Notes
        -----
        One-dimensional views will have an extra axis pre-pended to make them two-dimensional.
        E.g., rows and columns with shape (m,) will be re-shaped to (1, m) so that
        the `add_text` `row` and `column` parameters make sense.
        """
        return CanvasView(self.canvas)

    add_text = CanvasView.add_text

    def absolute_to_relative_coords(self, coords: Point):
        """
        Convert absolute coordinates to relative coordinates.
        """
        y, x = self.parent.absolute_to_relative_coords(coords)
        return Point(y - self.top, x - self.left)

    def collides_coords(self, coords: Point):
        """
        Return True if screen-coordinates are within bounding box.
        """
        y, x = self.absolute_to_relative_coords(coords)
        return 0 <= y < self.height and 0 <= x < self.width

    def collides_widget(self, widget):
        """
        Return True if some part of widget is within bounding box.
        """
        self_top, self_left, self_bottom, self_right, _, _ = self.absolute_rect
        other_top, other_left, other_bottom, other_right, _ , _ = widget.absolute_rect

        return not (
            self_top >= other_bottom
            or other_top >= self_bottom
            or self_left >= other_right
            or other_left >= self_right
        )

    def add_widget(self, widget):
        """
        Add a child widget.
        """
        self.children.append(widget)
        widget.parent = self
        widget.update_geometry()

    def add_widgets(self, *widgets):
        """
        Add multiple child widgets.
        """
        if len(widgets) == 1 and not isinstance(widgets[0], Widget):
            # Assume item is an iterable of widgets.
            widgets = widgets[0]

        for widget in widgets:
            self.add_widget(widget)

    def remove_widget(self, widget):
        """
        Remove widget.
        """
        self.children.remove(widget)
        widget.parent = None

    def pull_to_front(self, widget):
        """
        Move widget to end of widget stack so that it is drawn last.
        """
        self.children.remove(widget)
        self.children.append(widget)

    def walk_from_root(self):
        """
        Yield all descendents of the root widget.
        """
        for child in self.root.children:
            yield child
            yield from child.walk()

    def walk(self):
        """
        Yield self and all descendents.
        """
        for child in self.children:
            yield child
            yield from child.walk()

    def render(self, canvas_view, colors_view, rect: Rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, _, _ = rect
        index_rect = slice(t, b), slice(l, r)

        if self.is_transparent:
            source = self.canvas[index_rect]
            visible = source != " "  # " " isn't painted if transparent.

            canvas_view[visible] = source[visible]
            colors_view[visible] = self.colors[index_rect][visible]
        else:
            canvas_view[:] = self.canvas[index_rect]
            colors_view[:] = self.colors[index_rect]

        overlap = overlapping_region

        for child in self.children:
            if not child.is_visible or not child.is_enabled:
                continue

            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)

    def dispatch_press(self, key):
        """
        Dispatch key press until handled. (A key press is handled if a handler returns True.)
        """
        return (
            any(widget.dispatch_press(key) for widget in reversed(self.children) if widget.is_enabled)
            or self.on_press(key)
        )

    def dispatch_click(self, mouse_event):
        """
        Dispatch mouse event until handled. (A mouse event is handled if a handler returns True.)
        """
        return (
            any(widget.dispatch_click(mouse_event) for widget in reversed(self.children) if widget.is_enabled)
            or self.on_click(mouse_event)
        )

    def dispatch_paste(self, paste_event):
        """
        Dispatch paste event until handled.
        """
        return (
            any(widget.dispatch_paste(paste_event) for widget in reversed(self.children) if widget.is_enabled)
            or self.on_paste(paste_event)
        )

    def on_press(self, key: Key):
        """
        Handle key press. (Handled key presses should return True else False or None).
        """

    def on_click(self, mouse_event):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """

    def on_paste(self, paste_event):
        """
        Handle paste event.
        """


def overlapping_region(rect: Rect, child: Widget):
    """
    Find the overlapping region of a piece of screen and a child widget's canvas.
    """
    t, l, _, _, h, w = rect  # top, left, height, width

    ct = child.top - t
    cb = child.bottom - t
    cl = child.left - l
    cr = child.right - l

    if (
        ct >= h
        or cb < 0
        or cl >= w
        or cr < 0
    ):
        # Child doesn't overlap.
        return False

    ##################################################################
    # Four cases for top / bottom of child:                          #
    #     1) child top is off-screen and child bottom is off-screen. #
    #               +-------+                                        #
    #            +--| child |------------+                           #
    #            |  |       |   dest     |                           #
    #            +--|       |------------+                           #
    #               +-------+                                        #
    #     2) child top is off-screen and child bottom is on-screen.  #
    #               +-------+                                        #
    #            +--| child |------------+                           #
    #            |  +-------+   dest     |                           #
    #            +-----------------------+                           #
    #                                                                #
    #     3) child top is on-screen and child bottom is off-screen.  #
    #            +-----------------------+                           #
    #            |  +-------+   dest     |                           #
    #            +--| child |------------+                           #
    #               +-------+                                        #
    #                                                                #
    #     4) child top is on-screen and child bottom is on-screen.   #
    #            +-----------------------+                           #
    #            |  +-------+            |                           #
    #            |  | child |   dest     |                           #
    #            |  +-------+            |                           #
    #            +-----------------------+                           #
    #                                                                #
    # Similarly, by symmetry, four cases for left / right of child.  #
    ##################################################################

    # st, dt, sb, db, sl, dl, sr, dr stand for source_top, destination_top, source_bottom,
    # destination_bottom, source_left, destination_left, source_right, destination_right.
    if ct < 0:
        st = -ct
        dt = 0

        if cb >= h:
            sb = h + st
            db = h
        else:
            sb = child.height
            db = cb
    else:
        st =  0
        dt = ct

        if cb >= h:
            sb = h - dt
            db = h
        else:
            sb = child.height
            db = cb

    if cl < 0:
        sl = -cl
        dl = 0

        if cr >= w:
            sr = w + sl
            dr = w
        else:
            sr = child.width
            dr = cr
    else:
        sl = 0
        dl = cl

        if cr >= w:
            sr = w - dl
            dr = w
        else:
            sr = child.width
            dr = cr

    return (
        (slice(dt, db), slice(dl, dr)),
        Rect(st, sl, sb, sr, sb - st, sr - sl),
    )
