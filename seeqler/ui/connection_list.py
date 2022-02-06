import toga
from toga.style import Pack
from toga.constants import COLUMN, ROW, RIGHT

from .window import Window
from ..connection_manager import ConnectionManager, Connection


class ConnectionListWindow(Window):
    def __init__(self, app, **styling):
        self.lang = app.seeqler.lang

        super().__init__(app, self.lang.win_connection_list, "connection_list", (400, 500), resizable=False, **styling)

        self.tag_listbox = "connection list"
        self.tag_new_connection = "create connection"
        self.tag_connect_to = "connect to"

    def get_content(self) -> toga.Box:
        box = toga.Box("ConnListWindow", style=self.style)
        box.style.update(direction=COLUMN)

        wrapper = toga.Box("ConnListWrapper", style=self.style)
        wrapper.style.update(padding=10, direction=COLUMN)

        widget = toga.Label(self.lang.lbl_saved_connections, style=self.style)
        widget.style.update(padding_bottom=10)
        wrapper.add(widget)
        self.tbl_connection_list = toga.Table(
            headings=["UID", self.lang.txt_connection_label], id=self.tag_listbox, style=self.style
        )
        wrapper.add(self.tbl_connection_list)
        self.btn_connect = toga.Button(self.lang.btn_connect, style=self.style, on_press=self.ui_connect)

        box.add(wrapper)
        box.add(toga.Box(style=Pack(flex=1)))

        wrapper = toga.Box("ConnListNewConnection", style=self.style)
        wrapper.style.update(padding=10)

        widget = toga.Button(self.lang.btn_create_connection, style=self.style, on_press=self.ui_show_create_connection)
        widget.style.update(flex=1)

        wrapper.add(widget)
        box.add(wrapper)

        # with dpg.child_window(border=False, autosize_x=True, height=0.8 * self.height):
        #     with dpg.group(horizontal=False):
        #         with dpg.group(width=self.width):
        #             dpg.add_text("Список сохраненных подключений")
        #             dpg.add_listbox((), num_items=10, tag=self.tag_listbox)
        #         dpg.add_button(label="Подключиться", tag=self.tag_connect_to, callback=self.ui_connect)
        # with dpg.child_window(border=False, autosize_x=True, autosize_y=True):
        #     with dpg.group(horizontal=True):
        #         dpg.add_spacer(width=0.25 * self.relative_width)
        #         dpg.add_button(
        #             label="Создать новое подключение…",
        #             tag=self.tag_new_connection,
        #             width=0.75 * self.relative_width,
        #             callback=self.ui_show_create_connection,
        #         )
        return box

    def show(self) -> None:
        super().show()
        for x in ConnectionManager().list():
            self.tbl_connection_list.data.append(x.uuid, x.label)

    def ui_connect(self, button: toga.Widget) -> None:
        ...

    #     from .schema import SchemaWindow

    #     try:
    #         connection = ConnectionManager().get(label=dpg.get_value(self.tag_listbox))
    #         self.app.init(connection.connection_string)
    #         SchemaWindow(self.app).show()

    #     except ValueError as e:
    #         print(f"Can't connect to selected connection! Reason:\n{e}")

    def ui_show_create_connection(self) -> None:
        ...

    #     ConnectionCreateWindow(self.app).show()

    # class ConnectionCreateWindow(Window):
    #     def __init__(self, app, **kwargs):
    #         # fmt: off
    #         super().__init__(
    #             app, 'Новое подключение', 'connection_create', (600, 500), window_resizable=False,
    #             tag_input_label='tag label input', tag_connection_string='tag connection string',
    #             **kwargs
    #         )
    #         # fmt: on

    #     def create_connection(self):
    #         label = self.shift_value_to_unicode(dpg.get_value(self.tag_input_label))
    #         connection = self.shift_value_to_unicode(dpg.get_value(self.tag_connection_string))

    #         ConnectionManager().add(Connection(label, connection))
    #         self.close()

    #     def construct(self) -> None:
    #         dpg.add_text("Наименование подключения")
    #         dpg.add_input_text(tag=self.tag_input_label, width=self.relative_width)
    #         dpg.add_spacer(height=15)

    #         dpg.add_text("Строка подключения")
    #         dpg.add_input_text(tag=self.tag_connection_string, width=self.relative_width)
    #         dpg.add_spacer(height=15)

    #         with dpg.group(horizontal=True):
    #             dpg.add_button(label="Сохранить", callback=self.create_connection)
    #             dpg.add_button(label="Закрыть", callback=self.close)

    #     def close(self) -> None:
    #         ConnectionListWindow().show()
    #         dpg.delete_item(self.window_id)
    #         self.initiated = False
