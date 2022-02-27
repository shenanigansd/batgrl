from ...io import MouseEventType
from ..behaviors.grabbable_behavior import GrabbableBehavior
from ..behaviors.themable import Themable
from ..text_widget import TextWidget


class _IndicatorBehavior(Themable):
    """
    Common behavior for vertical and horizontal indicators.
    """
    def update_theme(self):
        ct = self.color_theme
        self.inactive_color = ct.primary_fg_light
        self.hover_color = ct.primary_bg
        self.active_color = ct.secondary_bg

        if not self.parent:
            self.colors[..., 3:] = self.inactive_color
        elif self.is_grabbed:
            self.colors[..., 3:] = self.active_color
        elif self.collides_point(self._last_mouse_pos):
            self.colors[..., 3:] = self.hover_color
        else:
            self.colors[..., 3:] = self.inactive_color

    def update_color(self, mouse_event):
        if self.collides_point(mouse_event.position):
            self.colors[..., 3:] = self.hover_color
        else:
            self.colors[..., 3:] = self.inactive_color

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.colors[..., 3:] = self.active_color

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self.update_color(mouse_event)

    def on_click(self, mouse_event):
        if super().on_click(mouse_event):
            return True

        if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            self.update_color(mouse_event)


class _VerticalIndicator(_IndicatorBehavior, GrabbableBehavior, TextWidget):
    def __init__(self):
        super().__init__(size=(2, 2))
        self.update_theme()

    def update_geometry(self):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent
        self.top = round(scroll_view.vertical_proportion * vertical_bar.fill_height)

    def grab_update(self, mouse_event):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent
        scroll_view.vertical_proportion += self.mouse_dy / vertical_bar.fill_height


class _HorizontalIndicator(_IndicatorBehavior, GrabbableBehavior, TextWidget):
    def __init__(self):
        super().__init__(size=(1, 4))
        self.update_theme()

    def update_geometry(self):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent
        self.left = round(scroll_view.horizontal_proportion * horizontal_bar.fill_width)

    def grab_update(self, mouse_event):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent
        scroll_view.horizontal_proportion += self.mouse_dx / horizontal_bar.fill_width
