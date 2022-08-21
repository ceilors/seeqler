from typing import TYPE_CHECKING, Callable, Iterable

import PyQt6.QtCore as core
import PyQt6.QtGui as gui
import PyQt6.QtWidgets as widget

from .utils import clear_layout
from ..sql.interface import Interface

if TYPE_CHECKING:
    from ..common.connection_manager import Connection

from inspect import signature
import uuid


class ConnStates:
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class Retriever(core.QObject):
    started = core.pyqtSignal()
    finished = core.pyqtSignal(object)
    progress = core.pyqtSignal(object)
    # TODO: exception raised finish

    def __init__(
        self,
        method: Callable,
        mth_args: Iterable | None = None,
        mth_kwargs: dict | None = None,
        extra_data: dict | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.method = method
        self.method_args = mth_args or list()
        self.method_kwargs = mth_kwargs or dict()
        self.extra_data = extra_data

    def run(self):
        self.started.emit()

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

    # region Engine and SQL requests

    def _run_next(self):
        # create thread and bind worker to it
        try:
            el = self._query.pop(0)
        except IndexError:
            self._executing_query = False
            return

        method, method_args, method_kwargs = el["method"], el.get("args", list()), el.get("kwargs", dict())
        prepare, report, process = el.get("prepare"), el.get("report"), el.get("process")
        extra_data = el.get("extra_data")

        run_uuid = uuid.uuid4()
        setattr(self, f"thread_{run_uuid}", core.QThread())
        qthread = getattr(self, f"thread_{run_uuid}")

        setattr(
            self,
            f"worker_{run_uuid}",
            Retriever(method, mth_args=method_args, mth_kwargs=method_kwargs, extra_data=extra_data),
        )
        worker = getattr(self, f"worker_{run_uuid}")
        worker.moveToThread(qthread)

        # connect Qt-signals to start work and clean up after it
        qthread.started.connect(worker.run)
        worker.finished.connect(qthread.quit)
        worker.finished.connect(worker.deleteLater)
        qthread.finished.connect(qthread.deleteLater)

        qthread.finished.connect(self._run_next)
        qthread.finished.connect(lambda: self._clean_up(run_uuid))

        # connect callbacks to signals
        if prepare:
            worker.started.connect(prepare)
        if report:
            worker.progress.connect(report)
        if process:
            worker.finished.connect(process)

        # start thread and worker
        qthread.start()

    def _clean_up(self, run_uuid: str):
        delattr(self, f"thread_{run_uuid}")
        delattr(self, f"worker_{run_uuid}")

    def run_parallel_task(
        self,
        method: Callable,
        method_args: Iterable | None = None,
        method_kwargs: dict | None = None,
        *,
        prepare: Callable | None = None,
        report: Callable | None = None,
        process: Callable | None = None,
        extra_data: dict | None = None,
    ):
        query_element = {"method": method}
        if method_args:
            query_element["args"] = method_args
        if method_kwargs:
            query_element["kwargs"] = method_kwargs
        if prepare:
            query_element["prepare"] = prepare
        if report:
            query_element["report"] = report
        if process:
            query_element["process"] = process
        if extra_data:
            query_element["extra_data"] = extra_data

        self._query.append(query_element)
        if not self._executing_query:
            self._run_next()

    def sql_connect(self):
        self.run_parallel_task(
            method=self.interface.connect, method_args=(self.connection,), process=self.sql_connect_after
        )

    @core.pyqtSlot(object)
    def sql_connect_after(self):
        self.state = ConnStates.CONNECTED
        self.sql_get_schema_names()

    def sql_get_schema_names(self):
        self.run_parallel_task(method=self.interface.get_schema_names, process=self.sql_get_schema_names_after)

    @core.pyqtSlot(object)
    def sql_get_schema_names_after(self, data: list):
        self.result_schema_names = data
        try:
            self.current_schema = data[0]
            self.sql_get_tables_from_schema(data[0])
        except IndexError:
            pass
        self.show_table_layout()

    def sql_get_tables_from_schema(self, name):
        self.run_parallel_task(
            method=self.interface.get_table_list, method_args=(name,), process=self.sql_get_tables_from_schema_after
        )

    @core.pyqtSlot(object)
    def sql_get_tables_from_schema_after(self, data: list):
        self.result_table_names = data
        self.widget_table_list.addItems(data)

    def sql_get_table_meta(self, name):
        self.run_parallel_task(
            method=lambda: self.interface.get_columns(name, schema=self.params_get_schema()),
            process=self.sql_get_table_meta_after,
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

    def sql_get_table_contents(self, name):
        self.run_parallel_task(
            method=self.interface.select,
            method_kwargs={"from_": name, "limit": 100},
            process=self.sql_get_table_contents_after,
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
