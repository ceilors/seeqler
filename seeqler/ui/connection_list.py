import toga
from toga.style import Pack
from toga.constants import COLUMN, ROW, RIGHT

from .window import Window
from ..connection_manager import ConnectionManager, Connection


class ConnectionListWindow(Window):
    def __init__(self, app, **kwargs):
        self.lang = app.seeqler.lang

        super().__init__(app, self.lang.win_connection_list, "connection_list", (400, 500), resizable=False, **kwargs)

    def get_content(self) -> toga.Box:
        box = toga.Box("ConnListWindow", style=Pack(direction=COLUMN))

        wrapper = toga.Box("ConnListWrapper", style=Pack(padding=10, direction=COLUMN))

        widget = toga.Label(self.lang.lbl_saved_connections, style=self.style)
        widget.style.update(padding_bottom=10)
        wrapper.add(widget)
        self.tbl_connection_list = toga.Table(
            headings=["UID", self.lang.txt_connection_label], id="connection list", style=self.style
        )
        wrapper.add(self.tbl_connection_list)
        self.btn_connect = toga.Button(self.lang.btn_connect, style=self.style, on_press=self.ui_connect)

        box.add(wrapper)
        box.add(toga.Box(style=Pack(flex=1)))

        wrapper = toga.Box("ConnListNewConnection", style=Pack(padding=10))

        widget = toga.Button(self.lang.btn_create_connection, style=self.style, on_press=self.ui_show_create_connection)
        widget.style.update(flex=1)

        wrapper.add(widget)
        box.add(wrapper)
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

    def ui_show_create_connection(self, widget: toga.Widget) -> None:
        ConnectionCreateWindow(self.app, modal=True).show()


class ConnectionCreateWindow(Window):
    def __init__(self, app, **kwargs):
        self.lang = app.seeqler.lang

        # fmt: off
        super().__init__(
            app, self.lang.win_create_connection, 'connection_create', (600, 500),
            resizable=False, minimizable=False, closeable=False,
            **kwargs
        )
        # fmt: on

    def create_connection(self, widget: toga.Widget):
        label = self.label_input.value
        connection = self.connstring_input.value

        ConnectionManager().add(Connection(label, connection))
        self.close()

    def get_content(self) -> toga.Box:
        box = toga.Box(style=Pack(direction=COLUMN))

        wrapper = toga.Box(style=Pack(direction=COLUMN, padding=10))

        wrapper.add(toga.Label(self.lang.lbl_connection_label, style=self.style))
        self.label_input = toga.TextInput(style=self.style)
        self.label_input.style.update(padding_bottom=15)
        wrapper.add(self.label_input)

        wrapper.add(toga.Label(self.lang.lbl_connection_string, style=self.style))
        self.connstring_input = toga.TextInput(style=self.style)
        wrapper.add(self.connstring_input)

        box.add(wrapper)

        box.add(toga.Box(style=Pack(flex=1)))

        wrapper = toga.Box(style=Pack(direction=ROW, padding=10))
        widget = toga.Button(self.lang.btn_save, on_press=self.create_connection, style=self.style)
        widget.style.update(flex=1)
        wrapper.add(widget)
        widget = toga.Button(self.lang.btn_close, on_press=self.close, style=self.style)
        widget.style.update(flex=1)
        wrapper.add(widget)

        box.add(wrapper)
        return box

    def close(self, widget: toga.Widget | None = None) -> None:
        self.window.close()
