from typing import Any, Optional, TYPE_CHECKING

import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

from ..common import SingletonMeta


TAG_DEFAULT_FONT = 'default font'


class Window(metaclass=SingletonMeta):
    """App window"""

    # fmt: off
    def __init__(
        self, inspector: Any | None, engine: Optional["Engine"],
        window_label: str, window_id: str, window_size: tuple[int, int],
        resize_viewport: bool = False, **kwargs,
    ):
        """
        Arguments:
            inspector: SQLAlchemy inspection result
            engine: SQLAlchemy database engine
            window_label: label for window
            window_id: window id used by dearpygui
            window_size (tuple[width, height]): window
            init_sequence: function to call when window is shown first time (item placement)
            resize_viewport: resize viewport to fit window
        """
        # fmt: on

        self.inspector = inspector
        self.engine = engine
        self.window_label = window_label
        self.window_id = window_id
        self.width, self.height = window_size
        self.resize_viewport = resize_viewport
        self.initiated = False

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self) -> str:
        return f'{self.window_label} ({self.window_id})'

    def construct(self) -> None:
        """Place items inside the window.

        This method is meant to be overridden in the successors.
        """
        return

    def _initiate(self) -> None:
        """Initiate window: create dpg.window and call self.construct"""
        if not self.initiated:
            with dpg.window(label=self.window_label, tag=self.window_id, width=self.width, height=self.height):
                dpg.bind_font(TAG_DEFAULT_FONT)
                self.construct()

            self.initiated = True

    def show(self) -> None:
        """Set window as dpg primary window. Resize viewport if needed.

        This method can be used in successors to fill up items with calculated data.
        """
        if not self.initiated:
            self._initiate()

        if window := dpg.get_active_window():
            dpg.hide_item(window)
        dpg.set_primary_window(self.window_id, True)

        if self.resize_viewport:
            dpg.set_viewport_width(self.width)
            dpg.set_viewport_height(self.height)
