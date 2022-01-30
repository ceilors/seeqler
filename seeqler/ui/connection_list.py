import dearpygui.dearpygui as dpg

from .window import Window
from ..connection_manager import ConnectionManager, Connection


class ConnectionListWindow(Window):
    def __init__(self, app, **kwargs):
        # fmt: off
        super().__init__(
            app, 'Список подключений', 'connection_list', (400, 500), window_resizable=False,
            tag_listbox='connection list', tag_new_connection='create connection', tag_connect_to='connect to',
            **kwargs
        )
        # fmt: on

    def construct(self) -> None:
        with dpg.child_window(border=False, autosize_x=True, height=0.8 * self.height):
            with dpg.group(horizontal=False):
                with dpg.group(width=self.width):
                    dpg.add_text('Список сохраненных подключений')
                    dpg.add_listbox((), num_items=10, tag=self.tag_listbox)
                dpg.add_button(label='Подключиться', tag=self.tag_connect_to, callback=self.ui_connect)
        with dpg.child_window(border=False, autosize_x=True, autosize_y=True):
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=0.25 * self.relative_width)
                dpg.add_button(
                    label='Создать новое подключение…',
                    tag=self.tag_new_connection,
                    width=0.75 * self.relative_width,
                    callback=self.ui_show_create_connection,
                )

    def show(self) -> None:
        super().show()
        connections = [x.label for x in ConnectionManager().list()]
        if not connections:
            dpg.configure_item(self.tag_connect_to, enabled=False)
        dpg.configure_item(self.tag_listbox, items=connections)

    def ui_connect(self) -> None:
        from .schema import SchemaWindow

        try:
            connection = ConnectionManager().get(label=dpg.get_value(self.tag_listbox))
            self.app.init(connection.connection_string)
            SchemaWindow(self.app).show()

        except ValueError as e:
            print(f"Can't connect to selected connection! Reason:\n{e}")

    def ui_show_create_connection(self) -> None:
        ConnectionCreateWindow(self.app).show()


class ConnectionCreateWindow(Window):
    def __init__(self, app, **kwargs):
        # fmt: off
        super().__init__(
            app, 'Новое подключение', 'connection_create', (600, 500), window_resizable=False,
            tag_input_label='tag label input', tag_connection_string='tag connection string',
            **kwargs
        )
        # fmt: on

    def create_connection(self):
        label = self.shift_value_to_unicode(dpg.get_value(self.tag_input_label))
        connection = self.shift_value_to_unicode(dpg.get_value(self.tag_connection_string))

        ConnectionManager().add(Connection(label, connection))
        self.close()

    def construct(self) -> None:
        dpg.add_text('Наименование подключения')
        dpg.add_input_text(tag=self.tag_input_label, width=self.relative_width)
        dpg.add_spacer(height=15)

        dpg.add_text('Строка подключения')
        dpg.add_input_text(tag=self.tag_connection_string, width=self.relative_width)
        dpg.add_spacer(height=15)

        with dpg.group(horizontal=True):
            dpg.add_button(label='Сохранить', callback=self.create_connection)
            dpg.add_button(label='Закрыть', callback=self.close)

    def close(self) -> None:
        ConnectionListWindow().show()
        dpg.delete_item(self.window_id)
        self.initiated = False
