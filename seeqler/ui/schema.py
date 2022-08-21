from typing import TYPE_CHECKING, Callable, Iterable

import PyQt6.QtCore as core
import PyQt6.QtGui as gui
import PyQt6.QtWidgets as widget

from .utils import clear_layout
from ..sql.interface import Interface

if TYPE_CHECKING:
    from ..common.connection_manager import Connection

from inspect import signature


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

        self.main_window = main_window
        self.settings = settings
        self.set_defaults()

        self.setFixedSize(core.QSize(800, 500))
        layout = widget.QHBoxLayout()
        layout.addWidget(self._get_loader())
        self.setLayout(layout)

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
        self.main_window.windows.connection_manager.show()
        super().hide()

    def show(self, *args, **kwargs):
        if not self.initiated:
            raise RuntimeError("Set up connection first!")
        super().show(*args, **kwargs)

    def get_default_tab_widget(self):
        tab = widget.QWidget()
        layout = widget.QVBoxLayout()
        layout.addWidget(self._get_loader())
        tab.setLayout(layout)
        return tab

    def show_table_layout(self):
        # region left_pane
        self.widget_schema_box = widget.QComboBox()
        if hasattr(self, "result_schema_names"):
            self.widget_schema_box.addItems(self.result_schema_names)
        self.widget_schema_box.currentIndexChanged.connect(self.event_change_schema)

        self.widget_table_list = widget.QListWidget()
        if hasattr(self, "result_table_names"):
            self.widget_table_list.addItems(self.result_table_names)
        self.widget_table_list.doubleClicked.connect(self.event_change_table)

        self.widget_disconnect_btn = widget.QPushButton(self.settings.lang.sw_btn_disconnect)

        left_pane = widget.QVBoxLayout()
        left_pane.addWidget(self.widget_schema_box)
        left_pane.addWidget(self.widget_table_list)
        left_pane.addWidget(self.widget_disconnect_btn)
        # endregion

        # region main_content
        self.widget_tab_holder = widget.QTabWidget()
        for tabname, tab in getattr(self, "widget_tabs", {}).items():
            self.widget_tab_holder.addTab(tab, tabname)
        else:
            self.widget_tab_holder.addTab(self.get_default_tab_widget(), "Пусто")
            self.widget_tabs = dict()

        main_content = widget.QVBoxLayout()
        main_content.addWidget(self.widget_tab_holder)
        # endregion

        layout = widget.QHBoxLayout()
        layout.addLayout(left_pane)
        layout.addLayout(main_content)
        layout.setStretchFactor(left_pane, 1)
        layout.setStretchFactor(main_content, 3)

        # deleting old layout
        clear_layout(self.layout())

        # setting new
        self.setLayout(layout)

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
        self.sql_get_table_meta(self.widget_table_list.item(idx.row()).text())

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
            method=lambda: self.interface.get_columns(name, schema=self.params_get_schema()),
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

        tab = widget.QTableWidget()
        tab.setColumnCount(len(columns))
        tab.setHorizontalHeaderLabels(x["name"] for x in columns)
        tab.setRowCount(10)
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

    def sql_get_table_contents(self, name):
        self.run_parallel_task(
            method=self.interface.select,
            method_kwargs={"from_": name, "limit": 100},
            at_end=self.sql_get_table_contents_after,
            extra_data={"name": name},
        )

    @core.pyqtSlot(object)
    def sql_get_table_contents_after(self, data: dict):
        table = data.get("name")
        contents = data.get("data")

        table: widget.QTableWidget = self.widget_tabs[table]
        table.setRowCount(len(contents))

        for row, data_row in enumerate(contents):
            for col, cell in enumerate(data_row):
                content = widget.QTableWidgetItem(str(cell))
                table.setItem(row, col, content)

    # endregion
