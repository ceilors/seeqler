import dearpygui.dearpygui as dpg

from .window import Window
from ..connection_manager import ConnectionManager


class ConnectionListWindow(Window):
    def __init__(self, **kwargs):
        """Calls Window.__init__ with specified arguments."""

        # fmt: off
        super().__init__(
            None, None, 'Список подключений', 'connection_list', (400, 500), False, True,
            tag_listbox='connection list', tag_newconnection='create connection', **kwargs
        )
        # fmt: on

    def construct(self) -> None:
        with dpg.child_window(border=False, autosize_x=True, height=0.8 * self.height):
            with dpg.group(horizontal=False):
                with dpg.group(width=self.width):
                    dpg.add_text('Список сохраненных подключений')
                    dpg.add_listbox((), num_items=10, tag=self.tag_listbox)
        with dpg.child_window(border=False, autosize_x=True, autosize_y=True):
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=0.25 * self.relative_width)
                dpg.add_button(
                    label='Создать новое подключение…',
                    tag=self.tag_newconnection,
                    width=0.75 * self.relative_width,
                    callback=self.ui_show_create_connection,
                )

    def show(self) -> None:
        super().show()
        dpg.configure_item(self.tag_listbox, items=[x.label for x in ConnectionManager().list()])

    def ui_show_create_connection(self) -> None:
        ...
