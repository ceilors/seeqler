import toga
from toga.style import Pack
from toga.constants import COLUMN, ROW, RIGHT

from .window import Window
from ..connection_manager import ConnectionManager, Connection


class ConnectionListWindow(Window):
    def __init__(self, app, **kwargs):
        self.lang = app.seeqler.lang

        super().__init__(
            app, self.lang.cl_win_connection_list, "connection_list", (400, 500), resizable=False, **kwargs
        )

    def get_content(self) -> toga.Box:
        root = toga.Box(style=Pack(direction=COLUMN))

        wrapper = toga.Box(style=Pack(padding=10, direction=COLUMN))

        widget = toga.Label(self.lang.cl_lbl_saved_connections, style=self.style)
        widget.style.update(padding_bottom=10)
        wrapper.add(widget)
        self.tbl_connection_list = toga.Table(
            headings=["UID", self.lang.cl_txt_connection_label],
            id="connection list",
            style=self.style,
            on_select=self.ui_enable_connect,
            missing_value="—",
        )
        wrapper.add(self.tbl_connection_list)
        self.btn_connect = toga.Button(
            self.lang.cl_btn_connect, style=self.style, on_press=self.ui_connect, enabled=False
        )
        self.btn_connect.style.update(padding_top=10)
        wrapper.add(self.btn_connect)

        root.add(wrapper)
        root.add(toga.Box(style=Pack(flex=1)))

        wrapper = toga.Box(style=Pack(padding=10))

        widget = toga.Button(
            self.lang.cl_btn_create_connection, style=self.style, on_press=self.ui_show_create_connection
        )
        widget.style.update(flex=1)

        wrapper.add(widget)
        root.add(wrapper)
        return root

    def ui_enable_connect(self, table, row=None):
        self.btn_connect.enabled = row is not None

    def show(self) -> None:
        super().show()
        for x in ConnectionManager().list():
            self.tbl_connection_list.data.append(x.uuid, x.label)

    def ui_connect(self, button: toga.Widget | None = None) -> None:
        from .schema import SchemaWindow

        try:
            connection = ConnectionManager().get(uuid=self.tbl_connection_list.selection.uid)
            self.app.seeqler.connect(connection.connection_string)

            schema_window = SchemaWindow(self.app)
            self.app.main_window = schema_window.get_window()
            schema_window.show()
            self.hide()
        except ValueError as e:
            self.window.error_dialog(
                self.lang.cl_err_cant_connect_title, self.lang.cl_err_cant_connect_message.format(error=e)
            )

    def ui_show_create_connection(self, button: toga.Widget | None = None) -> None:
        ConnectionCreateWindow(self.app, modal=True).show()


class ConnectionCreateWindow(Window):
    def __init__(self, app, **kwargs):
        self.lang = app.seeqler.lang

        # fmt: off
        super().__init__(
            app, self.lang.cl_win_create_connection, 'connection_create', (600, 500),
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

        wrapper.add(toga.Label(self.lang.cl_lbl_connection_label, style=self.style))
        self.label_input = toga.TextInput(style=self.style)
        self.label_input.style.update(padding_bottom=15)
        wrapper.add(self.label_input)

        wrapper.add(toga.Label(self.lang.cl_lbl_connection_string, style=self.style))
        self.connstring_input = toga.TextInput(style=self.style)
        wrapper.add(self.connstring_input)

        box.add(wrapper)

        box.add(toga.Box(style=Pack(flex=1)))

        wrapper = toga.Box(style=Pack(direction=ROW, padding=10))
        widget = toga.Button(self.lang.cl_btn_save, on_press=self.create_connection, style=self.style)
        widget.style.update(flex=1)
        wrapper.add(widget)
        widget = toga.Button(self.lang.cl_btn_close, on_press=self.close, style=self.style)
        widget.style.update(flex=1)
        wrapper.add(widget)

        box.add(wrapper)
        return box

    def close(self, widget: toga.Widget | None = None) -> None:
        self.window.close()
