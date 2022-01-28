from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg
from contextlib import nullcontext, AbstractContextManager

from ..common import SingletonMeta
from .font import TAG_DEFAULT_FONT, ENCODING_TRANSLITERATION

if TYPE_CHECKING:
    from ..app import Seeqler


class Window(metaclass=SingletonMeta):
    """App window"""

    window_attrs = {}

    def __init__(
        # fmt: off
        self, app: "Seeqler",
        window_label: str, window_id: str, window_size: tuple[int, int],
        *, window_resizable: bool = True, resize_viewport: bool = True,
        context: AbstractContextManager | None = None, **kwargs,
        # fmt: on
    ):
        """
        Arguments:
            app: Seeqler main app
            window_label: label for window
            window_id: window id used by dearpygui
            window_size (tuple[width, height]): window dimensions
            window_resizable: can user resize window
            resize_viewport: resize viewport to fit window
            kwargs: keyword args will be added to `self` directly. If key starts with `window_`,
                    argument will be added to `self.window_attrs`, which are passed to dpg.window creation
        """

        self.app = app
        self.window_label = window_label
        self.window_id = window_id
        self.width, self.height = window_size
        self.resizable = window_resizable
        self.resize_viewport = resize_viewport
        self.context = context if context else nullcontext()
        self.initiated = False

        for k, v in kwargs.items():
            if k.startswith('window_'):
                self.window_attrs[k.removeprefix('window_')] = v
                continue
            setattr(self, k, v)

    def __str__(self) -> str:
        return f'{self.window_label} ({self.window_id})'

    def construct(self) -> None:
        """Place items inside the window.

        This method is meant to be overridden in the successors.
        """
        return

    def shift_value_to_unicode(self, value: str) -> str:
        return value.translate(ENCODING_TRANSLITERATION)

    @property
    def relative_width(self) -> int:
        """Window width without paddings and spacings"""
        return self.width - (
            dpg.mvStyleVar_WindowPadding * 2 + dpg.mvStyleVar_ItemSpacing + dpg.mvStyleVar_ItemInnerSpacing
        )

    def _initiate(self) -> None:
        """Initiate window: create dpg.window and call self.construct"""
        if not self.initiated:
            with self.context:
                with dpg.window(
                    label=self.window_label,
                    tag=self.window_id,
                    width=self.width,
                    height=self.height,
                    no_resize=not self.resizable,
                    **self.window_attrs,
                ):
                    dpg.bind_font(TAG_DEFAULT_FONT)
                    self.construct()

            self.initiated = True

    @staticmethod
    def _hide_children(id: int | str) -> None:
        if not id:
            return
        try:
            if parent_id := dpg.get_item_info(id)['parent']:
                return Window._hide_children(parent_id)
        except SystemError:
            pass
        dpg.hide_item(id)

    @staticmethod
    def _show_children(id: int | str) -> None:
        if not id:
            return
        children = sum(dpg.get_item_info(id)['children'].values(), [])
        for child in children:
            Window._show_children(child)
        dpg.show_item(id)

    def show(self) -> None:
        """Set window as dpg primary window. Resize viewport if needed.

        This method can be used in successors to fill up items with calculated data.
        """
        if not self.initiated:
            self._initiate()

        if not self.window_attrs.get('modal', False):
            self._hide_children(dpg.get_active_window())
            self._show_children(self.window_id)
            dpg.set_primary_window(self.window_id, True)

            dpg.set_viewport_resizable(self.resizable)
            if self.resize_viewport:
                dpg.set_viewport_width(self.width)
                dpg.set_viewport_height(self.height)
