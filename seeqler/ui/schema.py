from typing import TYPE_CHECKING, Callable

import PyQt6.QtCore as core
import PyQt6.QtGui as gui
import PyQt6.QtWidgets as widget

from ..sql.interface import Interface

if TYPE_CHECKING:
    from ..common.connection_manager import Connection

from inspect import signature


class ConnStates:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class Retriever(core.QObject):
    finished = core.pyqtSignal()
    progress = core.pyqtSignal(dict)  # emit with some progress data to display

    def __init__(
        self, method: Callable, mth_args: list | None = None, mth_kwargs: dict | None = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.method = method
        self.method_args = mth_args or list()
        self.method_kwargs = mth_kwargs or dict()

    def run(self):
        if "signal" in signature(self.method).parameters:
            self.method(*self.method_kwargs, **self.method_kwargs, signal=self.progress)
        else:
            self.method(*self.method_kwargs, **self.method_kwargs)
        self.finished.emit()


class SchemaWindow(widget.QWidget):
    def __init__(self, main_window, settings):
        super().__init__()

        self.main_window = main_window
        self.settings = settings
        self.set_defaults()

        self.setFixedSize(core.QSize(800, 500))
        loader = widget.QLabel("...")  # TODO: replace with loading gif
        loader.setAlignment(core.Qt.AlignmentFlag.AlignCenter)
        layout = widget.QHBoxLayout()
        layout.addWidget(loader)
        self.setLayout(layout)

    def get_state_display(self):
        return self.settings.lang.get(f"sw_state_{self.state}")

    def set_defaults(self):
        self.initiated = False
        self.state = ConnStates.DISCONNECTED
        self.connection = None
        self.interface = None

    def set_up(self, connection: "Connection"):
        self.initiated = True
        self.connection = connection
        self.interface = Interface("sqlite")  # TODO: self.interface = Interface(connection.type)
        self.setWindowTitle(f"{connection.label} — {self.get_state_display()}")

    def hide(self, *args, **kwargs) -> None:
        self.set_defaults()
        super().hide(*args, **kwargs)

    def show(self, *args, **kwargs):
        if not self.initiated:
            raise RuntimeError("Set up connection first!")
        super().show(*args, **kwargs)

    def run_at_bg(
        self,
        method: Callable,
        method_args: list | None = None,
        method_kwargs: dict | None = None,
        *,
        prepare: Callable | None = None,
        report: Callable | None = None,
        process: Callable | None = None,
    ):
        # create thread and bind worker to it
        self.thread = core.QThread()
        self.worker = Retriever(method, mth_args=method_args, mth_kwargs=method_kwargs)
        self.worker.moveToThread(self.thread)

        # connect Qt-signals to start work and clean up after it
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # connect callbacks to signals
        if prepare:
            self.thread.started.connect(prepare)
        if report:
            self.worker.progress.connect(report)
        if process:
            self.thread.finished.connect(process)

        # start thread and worker
        self.thread.start()

    # def get_content(self) -> toga.Widget:
    #     root = toga.Box(style=Pack(direction=ROW))
    #
    #     left_side = toga.Box(style=Pack(padding=10, direction=COLUMN, width=200))
    #
    #     style = self.style
    #     style.update(padding_bottom=10)
    #
    #     left_side.add(toga.Label(self.lang.sw_lbl_schemas, style=style))
    #     self.schema_selector = toga.Table(
    #         [self.lang.sw_txt_schema_name], style=self.style, on_select=self.ui_select_schema, missing_value="—"
    #     )
    #     self.schema_selector.style.update(padding_bottom=15)
    #     left_side.add(self.schema_selector)
    #
    #     left_side.add(toga.Label(self.lang.sw_lbl_tables, style=style))
    #     self.table_selector = toga.Table([self.lang.sw_txt_table_name], style=self.style, missing_value="—")
    #     self.table_selector.style.update(padding_bottom=15)
    #     left_side.add(self.table_selector)
    #
    #     left_side.add(toga.Label(self.lang.sw_lbl_limit, style=style))
    #     self.limit_input = toga.NumberInput(style=style, default=10)
    #     self.limit_input.style.update(padding_bottom=30)
    #     left_side.add(self.limit_input)
    #
    #     left_side.add(toga.Button(self.lang.sw_btn_disconnect, style=self.style, on_press=self.ui_disconnect))
    #
    #     right_side = toga.Box(style=Pack(padding=10, direction=COLUMN))
    #
    #     toolbar = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
    #
    #     widget = toga.Button(
    #         self.lang.sw_btn_content_tab, id="btn_content", on_press=self.switch_tab, style=self.style
    #     )
    #     widget.style.update(padding_right=10)
    #     toolbar.add(widget)
    #     widget = toga.Button(self.lang.sw_btn_schema_tab, id="btn_schema", on_press=self.switch_tab, style=self.style)
    #     toolbar.add(widget)
    #
    #     right_side.add(toolbar)
    #
    #     self.tab_content = toga.Box(style=Pack(flex=1))
    #     right_side.add(self.tab_content)
    #
    #     split = toga.SplitContainer()
    #     split.content = [left_side, right_side]
    #
    #     root.add(split)
    #
    #     return root
    #
    # def switch_tab(self, button: toga.Button | None = None) -> None:
    #     tab = "content"
    #     if button:
    #         tab = str(button.id).split("_", maxsplit=1)[-1]
    #
    #     if not self.connection_params or self.current_content == tab:
    #         return
    #
    #     schema, table, limit = self.connection_params
    #     columns = self.app.seeqler.inspector.get_columns(table, schema=schema)
    #     if tab == "content":
    #         headers = [c["name"] for c in columns]
    #         data = []
    #
    #         with self.app.seeqler.engine.connect() as conn:
    #             for row in conn.execute(f"select * from {table} limit {limit}"):
    #                 data.append(row)
    #     else:
    #         headers = ["param", "type", "nullable", "default", "foreign key"]
    #         data = []
    #
    #         foreign_keys = {
    #             i["constrained_columns"][0]: "{referred_schema}.{referred_table}({referred_columns[0]})".format(**i)
    #             for i in self.app.seeqler.inspector.get_foreign_keys(table, schema=schema)
    #         }
    #         for item in columns:
    #             data.append(
    #                 [item["name"], item["type"], item["nullable"], item["default"], foreign_keys.get(item["name"])]
    #             )
    #
    #     self.current_content = tab
    #     self.tab_content.add(toga.Table(headings=headers, style=self.style, data=data, missing_value="—"))
    #
    # def show(self) -> None:
    #     super().show()
    #     names = self.app.seeqler.inspector.get_schema_names()
    #     for name in names:
    #         self.schema_selector.data.append(name)
    #
    # def ui_disconnect(self, widget=None) -> None:
    #     conn_list = ConnectionListWindow(self.app)
    #     self.app.main_window = conn_list.get_window()
    #     conn_list.show()
    #     self.app.seeqler.engine = None
    #     self.app.seeqler.inspector = None
    #     self.hide()
    #
    # def _get_schema_name(self, row=None) -> str | None:
    #     if not row:
    #         row = self.schema_selector.selection
    #     return getattr(row, self.lang.sw_txt_schema_name.lower(), None)
    #
    # def _get_table_name(self, row=None) -> str | None:
    #     if not row:
    #         row = self.table_selector.selection
    #     return getattr(row, self.lang.sw_txt_table_name.lower(), None)
    #
    # def ui_select_schema(self, table, row):
    #     """Select schema from schemas list."""
    #
    #     name = self._get_schema_name(row)
    #     if not name:
    #         return
    #
    #     items = sorted(self.app.seeqler.inspector.get_table_names(schema=name))
    #     for item in items:
    #         self.table_selector.data.append(item)
    #
    # def ui_select_table(self, table, row):
    #     """Select table from schema and initiate tab panel"""
    #     self.tab_content.remove(*self.tab_content.children)
    #
    #     schema = self._get_schema_name()
    #     if not schema:
    #         return
    #
    #     table_name = self._get_table_name(row)
    #     if not table_name:
    #         return
    #
    #     limit = self.limit_input.value
    #
    #     self.connection_params = {"schema": schema, "table": table_name, "limit": limit}
    #     self.current_content = ""  # clean current_content to update widget
    #     self.switch_tab()
