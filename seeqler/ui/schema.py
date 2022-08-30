from typing import TYPE_CHECKING, Callable, Iterable, Any

import PyQt6.QtCore as core
import PyQt6.QtGui as gui
import PyQt6.QtWidgets as widget

from .utils import clear_layout
from ..sql.interface import Interface

if TYPE_CHECKING:
    from ..common.connection_manager import Connection

from inspect import signature


BTN_AT_RIGHT = widget.QTabBar.ButtonPosition.RightSide


class ConnStates:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class Retriever(core.QObject):
    """
    Background task worker
    """

    started = core.pyqtSignal()
    finished = core.pyqtSignal(object)
    progress = core.pyqtSignal(object)
    # TODO: signal to emit after exception raised

    def __init__(
        self,
        method: Callable,
        mth_args: Iterable | None = None,
        mth_kwargs: dict | None = None,
        extra_data: dict | None = None,
        *args,
        **kwargs,
    ):
        """
        Background task worker. Gets ``method`` from args and runs it with ``mth_args`` and ``mth_kwargs`` passed
        to it. If ``extra_data`` is presented, result will contain a copy of it: thus some data can be transferred
        between "begin" and "end" events.

        Method can have ``signal`` argument — it can be used to emit ``progress`` signal to show some data while
        main task is still executing.

        Args:
            method: method to run
            mth_args: positional arguments
            mth_kwargs: keyword arguments
            extra_data: dict of extra data to pass to finished signal
        """
        super().__init__(*args, **kwargs)

        self.method = method
        self.method_args = mth_args or list()
        self.method_kwargs = mth_kwargs or dict()
        self.extra_data = extra_data

    def run(self) -> None:
        """
        Run method from worker.
        """
        self.started.emit()

        # check if method accepts "signal" argument
        if "signal" in signature(self.method).parameters:
            data = self.method(*self.method_args, **self.method_kwargs, signal=self.progress)
        else:
            data = self.method(*self.method_args, **self.method_kwargs)

        if self.extra_data:
            data = self.extra_data | {"data": data}

        self.finished.emit(data)


class SchemaWindow(widget.QWidget):
    _state = ConnStates.DISCONNECTED
    _query, _executing_query = [], False
    to_clean = []

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        title = self.settings.lang.get(f"sw_state_{self.state}")
        if hasattr(self, "connection") and self.connection:
            self.setWindowTitle(f"{self.connection.label} — {title}")
        else:
            self.setWindowTitle(title)

    def _get_loader(self) -> widget.QWidget:
        loader = widget.QLabel("...")  # TODO: replace with loading gif
        loader.setAlignment(core.Qt.AlignmentFlag.AlignCenter)
        return loader

    def __init__(self, main_window, settings):
        super().__init__()

        self.setObjectName("SchemaWindow")
        self.main_window = main_window
        self.settings = settings
        self.set_defaults()

        self.resize(core.QSize(int(settings.screen_width * 0.65), int(settings.screen_height * 0.65)))
        layout = widget.QHBoxLayout()
        layout.addWidget(self._get_loader())
        self.setLayout(layout)

    def clear(self):
        clear_layout(self.layout())
        for item in self.to_clean:
            if hasattr(self, item):
                delattr(self, item)

    def set_defaults(self):
        self.initiated = False
        self.state = ConnStates.DISCONNECTED
        self.connection = None
        self.interface = None

    def set_up(self, connection: "Connection"):
        self.initiated = True
        self.connection = connection
        self.interface = Interface("sqlite")  # TODO: self.interface = Interface(connection.type)
        self.state = ConnStates.DISCONNECTED
        self.sql_connect()

    def closeEvent(self, event):
        self.set_defaults()
        self.clear()
        self.main_window.windows.connection_manager.show()
        super().hide()

    def show(self, *args, **kwargs):
        if not self.initiated:
            raise RuntimeError("Set up connection first!")
        super().show(*args, **kwargs)

    def show_table_layout(self):
        # region left_pane
        self.widget_schema_box = widget.QComboBox()
        if hasattr(self, "result_schema_names"):
            self.widget_schema_box.addItems(self.result_schema_names)
        self.widget_schema_box.currentIndexChanged.connect(self.event_change_schema)
        self.to_clean.extend(("widget_schema_box", "result_schema_names"))

        self.widget_table_list = widget.QListWidget()
        if hasattr(self, "result_table_names"):
            self.widget_table_list.addItems(self.result_table_names)
        self.widget_table_list.doubleClicked.connect(self.event_change_table)
        self.to_clean.extend(("widget_table_list", "result_table_names"))

        self.widget_disconnect_btn = widget.QPushButton(self.settings.lang.sw_btn_disconnect)
        self.widget_disconnect_btn.clicked.connect(lambda: self.closeEvent(None))
        self.to_clean.append("widget_disconnect_btn")

        self.widget_filter = widget.QLineEdit()
        self.widget_filter.textChanged.connect(self.filter_table_list)

        left_pane = widget.QVBoxLayout()
        left_pane.addWidget(self.widget_filter)
        left_pane.addWidget(self.widget_schema_box)
        left_pane.addWidget(self.widget_table_list)
        left_pane.addWidget(self.widget_disconnect_btn)
        # endregion

        # region right_pane
        self.widget_tab_holder = widget.QTabWidget()
        self.widget_tab_holder.setObjectName("WidgetTabHolder")
        self.widget_tab_holder.setTabsClosable(True)
        self.widget_tab_holder.tabCloseRequested.connect(self.tab_close)

        self.widget_tab_holder.addTab(self.create_tab(default=True), "Пусто")
        self.widget_tab_holder.tabBar().setTabButton(0, BTN_AT_RIGHT, None)
        self.widget_tabs = dict()

        self.to_clean.extend(("widget_tab_holder", "widget_tabs"))

        right_pane = widget.QVBoxLayout()
        right_pane.addWidget(self.widget_tab_holder)
        # endregion

        layout = widget.QHBoxLayout()
        left_pane.setContentsMargins(10, 10, 0, 10)
        right_pane.setContentsMargins(10, 10, 10, 10)

        self.left_pane_widget = widget.QWidget()
        self.left_pane_widget.setObjectName("SchemaLeftPane")
        self.left_pane_widget.setLayout(left_pane)
        self.left_pane_widget.setMaximumWidth(300)

        self.right_pane_widget = widget.QWidget()
        self.right_pane_widget.setObjectName("SchemaRightPane")
        self.right_pane_widget.setLayout(right_pane)

        self.to_clean.extend(("left_pane_widget", "right_pane_widget"))

        layout.addWidget(self.left_pane_widget, 1)
        layout.addWidget(self.right_pane_widget, 3)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # deleting old layout
        clear_layout(self.layout())

        # setting new
        self.setLayout(layout)

    def filter_table_list(self, text):
        for index in range(self.widget_table_list.count()):
            item = self.widget_table_list.item(index)
            item.setHidden(text not in item.text())

    # region Tab GUI

    def create_tab(self, table_name: str = None, columns: list[dict] = None, default=False):
        if default or columns is None or table_name is None:
            return self.get_default_tab_widget()

        tab = widget.QWidget()
        layout = widget.QVBoxLayout()

        tab.offset = 0  # offset of table data

        tab.table = widget.QTableWidget()
        tab.table.setColumnCount(len(columns))
        tab.table.setHorizontalHeaderLabels(x["name"] for x in columns)
        tab.table.setRowCount(5)  # default row count until table is filled up
        tab.table.resizeColumnsToContents()
        tab.table.setWordWrap(False)

        bottom_layout = widget.QHBoxLayout()

        tab.statusbar = widget.QLabel()
        tab.statusbar.setText(f"1-? {self.settings.lang.sw_tab_statusbar_of} ?")
        tab.statusbar.setAlignment(core.Qt.AlignmentFlag.AlignCenter)

        bottom_layout.addWidget(tab.statusbar, alignment=core.Qt.AlignmentFlag.AlignCenter)

        tab.btn_left = widget.QPushButton()
        tab.btn_left.setText(self.settings.lang.sw_tab_statusbar_left)
        tab.btn_left.clicked.connect(lambda: self.change_table_page(table_name, -1))
        tab.btn_left.setDisabled(True)

        tab.btn_right = widget.QPushButton()
        tab.btn_right.setText(self.settings.lang.sw_tab_statusbar_right)
        tab.btn_right.clicked.connect(lambda: self.change_table_page(table_name, 1))
        tab.btn_right.setDisabled(True)

        bottom_layout.insertWidget(0, tab.btn_left, alignment=core.Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(tab.btn_right, alignment=core.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(tab.table)
        layout.addLayout(bottom_layout)
        tab.setLayout(layout)
        return tab

    def fillup_table(self, table_name: str, data: list[list[Any]]):
        tab = self.widget_tabs[table_name]

        contents = data["contents"]
        row_number = data["rows"]
        table_rows = len(contents)
        current_rows = tab.offset + table_rows

        tab.table.setRowCount(table_rows)
        tab.table.scrollToTop()

        for row, data_row in enumerate(contents):
            for col, cell in enumerate(data_row):
                content = widget.QTableWidgetItem(str(cell))
                tab.table.setItem(row, col, content)

        methods = {True: "setEnabled", False: "setDisabled"}

        getattr(tab.btn_left, methods[tab.offset >= self.settings.rows_per_page])(True)
        getattr(tab.btn_right, methods[current_rows != row_number])(True)

        tab.statusbar.setText(f"{tab.offset + 1}-{current_rows} {self.settings.lang.sw_tab_statusbar_of} {row_number}")

        if row_number == 0:
            tab.statusbar.setText(f"0 {self.settings.lang.sw_tab_statusbar_of} 0")

    def change_table_page(self, table_name: str, sign: int):
        tab = self.widget_tabs[table_name]

        tab.offset += sign * self.settings.rows_per_page
        self.sql_get_table_contents(table_name, tab.offset)

    def get_default_tab_widget(self):
        tab = widget.QWidget()
        layout = widget.QVBoxLayout()
        layout.addWidget(self._get_loader())
        tab.setLayout(layout)
        return tab

    def tab_close(self, idx: int):
        tab = self.widget_tab_holder.tabBar().tabText(idx)
        del self.widget_tabs[tab]

        self.widget_tab_holder.removeTab(idx)

        if not self.widget_tabs:
            self.widget_tab_holder.addTab(self.create_tab(default=True), "Пусто")
            self.widget_tab_holder.tabBar().setTabButton(0, BTN_AT_RIGHT, None)

    # endregion

    # region Params

    def params_get_schema(self) -> str | None:
        if not hasattr(self, "widget_schema_box"):
            return None
        return self.widget_schema_box.currentText()

    # endregion

    # region Events

    def event_disconnect(self):
        self.interface.disconnect()
        self.closeEvent(None)

    def event_change_schema(self, idx: int = None):
        self.widget_table_list.clear()
        # or can load text via self.widget_schema_box.itemText(idx)
        self.sql_get_tables_from_schema(self.widget_schema_box.currentText())

    def event_change_table(self, idx: core.QModelIndex):
        text = self.widget_table_list.item(idx.row()).text()

        if text in getattr(self, "widget_tabs", {}):
            self.widget_tab_holder.setCurrentWidget(self.widget_tabs[text])
        else:
            self.sql_get_table_meta(text)

    # endregion

    # region Background tasks

    def _run_next(self) -> None:
        """
        Run next element of task query.
        """

        try:
            el = self._query.pop(0)
        except IndexError:
            self._executing_query = False
            return

        if self._executing_query:
            return

        method, method_args, method_kwargs = el["method"], el.get("args", list()), el.get("kwargs", dict())
        at_start, progress, at_end = el.get("at_start"), el.get("progress"), el.get("at_end")
        extra_data = el.get("extra_data")

        # create thread and worker, move worker to thread
        self.thread = core.QThread()
        self.worker = Retriever(method, mth_args=method_args, mth_kwargs=method_kwargs, extra_data=extra_data)
        self.worker.moveToThread(self.thread)

        # connect Qt-signals to start work and clean up after it
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        # qt deletion
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # manual deletion and run next step
        self.thread.finished.connect(self._clean_up)

        # connect callbacks to signals
        if at_start:
            self.worker.started.connect(at_start)
        if progress:
            self.worker.progress.connect(progress)
        if at_end:
            self.worker.finished.connect(at_end)

        # start thread and worker
        self.thread.start()
        self._executing_query = True

    def _clean_up(self) -> None:
        """
        Delete obsolete threads and workers. Stop executing query and try to execute next element of it.
        """
        del self.thread
        del self.worker
        self._executing_query = False
        self._run_next()

    def run_parallel_task(
        self,
        method: Callable,
        method_args: Iterable | None = None,
        method_kwargs: dict | None = None,
        *,
        at_start: Callable | None = None,
        progress: Callable | None = None,
        at_end: Callable | None = None,
        extra_data: dict | None = None,
    ) -> None:
        """
        Adds new element to query of background tasks to run to. All the elements will be executed one by one at new
        threads using Retriever-class workers.

        If query is executing at the moment, new element will be just pushed to end of it. Otherwise, new element
        will be run immediately.

        Args:
            method: function to run
            method_args: positional arguments to pass to function
            method_kwargs: keyword arguments to pass to function
            at_start: function to run when Retriever.started signal is emitted
            progress: function to run when Retriever.progress signal is emitted
            at_end: function to run when Retriever.finished signal is emitted
            extra_data: data to pass to "at_end" function besides task result
        """

        query_element = {"method": method}
        if method_args:
            query_element["args"] = method_args
        if method_kwargs:
            query_element["kwargs"] = method_kwargs
        if at_start:
            query_element["at_start"] = at_start
        if progress:
            query_element["progress"] = progress
        if at_end:
            query_element["at_end"] = at_end
        if extra_data:
            query_element["extra_data"] = extra_data

        self._query.append(query_element)
        if not self._executing_query:
            self._run_next()

    # endregion

    # region Engine and SQL requests

    def sql_connect(self):
        self.run_parallel_task(
            method=self.interface.connect, method_args=(self.connection,), at_end=self.sql_connect_after
        )

    @core.pyqtSlot(object)
    def sql_connect_after(self):
        self.state = ConnStates.CONNECTED
        self.sql_get_schema_names()

    # -----

    def sql_get_schema_names(self):
        self.run_parallel_task(method=self.interface.get_schema_names, at_end=self.sql_get_schema_names_after)

    @core.pyqtSlot(object)
    def sql_get_schema_names_after(self, data: list):
        self.result_schema_names = data
        try:
            self.current_schema = data[0]
            self.sql_get_tables_from_schema(data[0])
        except IndexError:
            pass
        self.show_table_layout()

    # -----

    def sql_get_tables_from_schema(self, name):
        self.run_parallel_task(
            method=self.interface.get_table_list, method_args=(name,), at_end=self.sql_get_tables_from_schema_after
        )

    @core.pyqtSlot(object)
    def sql_get_tables_from_schema_after(self, data: list):
        self.result_table_names = data
        self.widget_table_list.addItems(data)

    # -----

    def sql_get_table_meta(self, name):
        self.run_parallel_task(
            method=lambda: self.interface.get_table_columns(name, schema=self.params_get_schema()),
            at_end=self.sql_get_table_meta_after,
            extra_data={"name": name},
        )

    @core.pyqtSlot(object)
    def sql_get_table_meta_after(self, data: dict):
        table = data.get("name")
        columns = data.get("data")

        if not getattr(self, "widget_tabs", None):
            self.widget_tab_holder.removeTab(0)
            self.widget_tabs = dict()

        tab = self.create_tab(table, columns)
        self.widget_tabs[table] = tab
        self.widget_tab_holder.addTab(tab, table)
        self.widget_tab_holder.setCurrentWidget(tab)

        # getting meta info about table:
        # headers = ["param", "type", "nullable", "default", "foreign key"]
        # data = []
        #
        # foreign_keys = {
        #     i["constrained_columns"][0]: "{referred_schema}.{referred_table}({referred_columns[0]})".format(**i)
        #     for i in self.app.seeqler.inspector.get_foreign_keys(table, schema=schema)
        # }
        # for item in columns:
        #     data.append(
        #         [item["name"], item["type"], item["nullable"], item["default"], foreign_keys.get(item["name"])]
        #     )

        self.sql_get_table_contents(table)

    # -----

    def sql_get_table_contents(self, name, offset: int = 0):
        self.run_parallel_task(
            method=self.interface.get_table_data,
            method_kwargs={"table": name, "offset": offset, "limit": self.settings.rows_per_page},
            at_end=self.sql_get_table_contents_after,
            extra_data={"name": name},
        )

    @core.pyqtSlot(object)
    def sql_get_table_contents_after(self, data: dict):
        table_name = data.get("name")
        contents = data.get("data")

        self.fillup_table(table_name, contents)

    # endregion
