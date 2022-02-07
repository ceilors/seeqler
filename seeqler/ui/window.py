from typing import Callable

import toga

from ..common import SingletonMeta


class Window(metaclass=SingletonMeta):
    """App window"""

    style = None

    def __init__(
        # fmt: off
        self, app: toga.App, title: str, id: str, size: tuple[int, int],
        *, position: tuple[int, int] | None = None, toolbar: list[toga.Widget] | None = None, resizable: bool = True,
        closeable: bool = True, minimizable: bool = True, on_close: Callable | None = None, modal: bool = False,
        hide_app_name: bool = False, **styling,
        # fmt: on
    ):
        """
        Arguments:
            app: toga application
            title: label for window
            id: window ID
            size: size of window in pixels as (width, height)
            position: position of window on screen as (x, y). Window will be centered if None is passed
            toolbar: list of toga.Widget to add to window toolbar
            resizable: if window is resizable
            closeable: if window is closeable
            minimizable: if window is minimizable
            on_close: handler to call when window is closed
            styling: keyword args will be added to `self.style`.
        """

        self.app = app
        self.id = id
        self.width, self.height = size
        self.modal = modal

        if position is None:
            position = (100, 100)  # TODO: center window

        self.style = self.app.default_style

        for k, v in styling.items():
            setattr(self.style, k, v)

        title = title if hide_app_name else f"{title} | Seeqler"

        # fmt: off
        self.window = toga.Window(
            id, title, position, size, toolbar=toolbar, resizeable=resizable, closeable=closeable,
            minimizable=minimizable, on_close=on_close
        )
        # fmt: on

        try:
            app.windows += self.window
        except:
            pass

        self.initiated = False

    def __str__(self) -> str:
        return f"{self.window.title} ({self.window.id})"

    def get_content(self) -> toga.Widget:
        """Place items inside the window.

        This method is meant to be overridden in the successors.
        """
        return toga.Box("WindowEmptyContent")

    def _initiate(self) -> None:
        """Initiate window: create fill up self.window with content"""
        if not self.initiated:
            self.window.content = self.get_content()
            self.initiated = True

    def get_window(self) -> toga.Window:
        """Get the instance-bound toga window"""
        if not self.initiated:
            self._initiate()
        return self.window

    def show(self) -> None:
        """Set window as dpg primary window. Resize viewport if needed.

        This method can be used in successors to fill up items with calculated data.
        """
        if not self.initiated:
            self._initiate()

        # if not self.modal:
        #     self.app.main_window = self.get_window()
        self.window.show()

    def hide(self) -> None:
        self.window.close()
