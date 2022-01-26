import dearpygui.dearpygui as dpg

from .window import Window
from ..connection_manager import ConnectionManager


class ConnectionListWindow(Window):
    def __init__(self, **kwargs):
        """Calls Window.__init__ with specified arguments."""

        # fmt: off
        super().__init__(
            None, None, 'Список подключений', 'connection_list', (400, 600), True,
            tag_listbox='connection list'
        )
        # fmt: on

    def construct(self) -> None:
        with dpg.group(horizontal=False):
            with dpg.group(width=400):
                dpg.add_text('Список сохраненных подключений')
                dpg.add_listbox((), tag=self.tag_listbox)  # , callback=...)
            dpg.add_button(label='Создать новое подключение...')

    def show(self) -> None:
        super().show()
        dpg.configure_item(self.tag_listbox, items=[x.label for x in ConnectionManager().list()])
