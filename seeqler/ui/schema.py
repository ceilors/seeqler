from typing import TYPE_CHECKING, Callable, Iterable, Any

from .custom import SeeqlerTab
from .utils import clear_layout
from ..common.language import Language
from ..settings import Settings
from ..sql.interface import Interface

from inspect import signature
from PyQt6 import QtCore as core, QtGui as gui, QtWidgets as widget

if TYPE_CHECKING:
    from ..common.connection_manager import Connection


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
    _raw_sql_counter = -1
    to_clean = []

    # region initial

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

    @property
    def raw_sql(self) -> int:
        self._raw_sql_counter += 1
        return self._raw_sql_counter

    def _get_loader(self) -> widget.QWidget:
        loader = widget.QLabel("...")  # TODO: replace with loading gif
        loader.setAlignment(core.Qt.AlignmentFlag.AlignCenter)
        return loader

    def __init__(self, main_window):
        super().__init__()

        self.setObjectName("SchemaWindow")
        self.main_window = main_window
        self.settings = Settings()
        self.lang = Language()
        self.set_defaults()

        self.resize(core.QSize(int(self.settings.screen_width * 0.65), int(self.settings.screen_height * 0.65)))
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

    # endregion

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

        # self.widget_disconnect_btn = widget.QPushButton(self.settings.lang.sw_btn_disconnect)
        # self.widget_disconnect_btn.clicked.connect(lambda: self.closeEvent(None))
        # self.to_clean.append("widget_disconnect_btn")

        self.widget_filter = widget.QLineEdit()
        self.widget_filter.setPlaceholderText(self.settings.lang.sw_widget_filter_placeholder)
        self.widget_filter.textChanged.connect(self.filter_table_list)

        left_pane = widget.QVBoxLayout()
        left_pane.addWidget(self.widget_filter)
        left_pane.addWidget(self.widget_table_list)
        # left_pane.addWidget(self.widget_disconnect_btn)
        left_pane.addWidget(self.widget_schema_box)
        # endregion

        # region right_pane
        self.widget_tab_holder = widget.QTabWidget()
        self.widget_tab_holder.setObjectName("WidgetTabHolder")
        self.widget_tab_holder.setTabsClosable(True)
        self.widget_tab_holder.tabCloseRequested.connect(self.tab_close)

        self.widget_tab_holder.addTab(self.create_tab(default=True), self.lang.sw_widget_tab_holder_empty)
        self.widget_tab_holder.tabBar().setTabButton(0, BTN_AT_RIGHT, None)
        self.widget_tabs: dict[str, SeeqlerTab] = dict()

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

        # region top toolbar
        self.toolbar_wrapper = widget.QFrame()
        self.toolbar_wrapper.setFrameShape(widget.QFrame.Shape.StyledPanel)
        sql_raw = widget.QToolButton(self.toolbar_wrapper)
        sql_raw.setIcon(gui.QIcon(str(self.settings.resources_path / "icons" / "raw_sql.png")))
        sql_raw.clicked.connect(
            lambda: self.create_tab(f"__sql_raw_{self.raw_sql}", raw=True, title=self.lang.sw_widget_tab_holder_raw)
        )
        self.toolbar_wrapper.setMaximumHeight(22)
        self.toolbar_wrapper.setMinimumHeight(22)
        # endregion

        general_layout = widget.QVBoxLayout()
        general_layout.addWidget(self.toolbar_wrapper)
        general_layout.addLayout(layout)
        general_layout.setSpacing(0)
        general_layout.setContentsMargins(0, 0, 0, 0)

        # deleting old layout
        clear_layout(self.layout())

        # setting new
        self.setLayout(general_layout)

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

    def filter_table_list(self, text):
        for index in range(self.widget_table_list.count()):
            item = self.widget_table_list.item(index)
            item.setHidden(text not in item.text())

    # endregion

    # region Tab GUI

    def create_tab(
        self, table_name: str = None, columns: list[dict] = None, *, raw=False, default=False, title: str = None
    ):
        if default or columns is None and not raw or table_name is None:
            return self.get_default_tab_widget()

        tab = SeeqlerTab(self, table_name, columns, raw=raw)

        if not getattr(self, "widget_tabs", None):
            self.widget_tab_holder.removeTab(0)
            self.widget_tabs: dict[str, SeeqlerTab] = dict()

        self.widget_tabs[table_name] = tab
        self.widget_tab_holder.addTab(tab, title if title else table_name)
        self.widget_tab_holder.setCurrentWidget(tab)
        tab.focus()
        return tab

    def fillup_table(self, table_name: str, data: list[list[Any]]):
        tab = self.widget_tabs[table_name]
        tab.fillup_table(data)

    def get_default_tab_widget(self):
        tab = widget.QWidget()
        layout = widget.QVBoxLayout()
        layout.addWidget(self._get_loader())
        tab.setLayout(layout)
        return tab

    def tab_close(self, idx: int):
        tab: SeeqlerTab = self.widget_tab_holder.widget(idx)
        del self.widget_tabs[tab.table_name]

        self.widget_tab_holder.removeTab(idx)

        if not self.widget_tabs:
            self.widget_tab_holder.addTab(self.create_tab(default=True), "Пусто")
            self.widget_tab_holder.tabBar().setTabButton(0, BTN_AT_RIGHT, None)

    # endregiond

    # region Params

    def params_get_schema(self) -> str | None:
        if not hasattr(self, "widget_schema_box"):
            return None
        return self.widget_schema_box.currentText()

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
        self.run_parallel_task(
            method=self.interface.inspector.get_schema_names, at_end=self.sql_get_schema_names_after
        )

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
            method=self.interface.inspector.get_table_names,
            method_args=(name,),
            at_end=self.sql_get_tables_from_schema_after,
        )

    @core.pyqtSlot(object)
    def sql_get_tables_from_schema_after(self, data: list):
        self.result_table_names = sorted(data)
        self.widget_table_list.addItems(data)

    # -----

    def sql_get_table_meta(self, name):
        def method(table, schema=None):
            cols = self.interface.inspector.get_columns(table, schema=schema)
            fkeys = {
                fk["constrained_columns"][0]: "{referred_schema}.{referred_table}({referred_columns[0]})".format(**fk)
                for fk in self.interface.inspector.get_foreign_keys(table, schema=schema)
            }

            for col in cols:
                col["fkey"] = fkeys.get(col["name"])
            return cols

        self.run_parallel_task(
            method=method,
            method_args=(name, self.params_get_schema()),
            at_end=self.sql_get_table_meta_after,
            extra_data={"name": name},
        )

    @core.pyqtSlot(object)
    def sql_get_table_meta_after(self, data: dict):
        table = data.get("name")
        columns = data.get("data")
        tab = self.create_tab(table, columns)
        tab.load_table_contents()

    # -----

    def sql_get_table_contents(self, name, offset: int = 0, limit: int = 100, select: str = "*"):
        def get_table_data(table: str, limit_: int, offset_: int, select_: str):
            data, _ = self.interface.select(what=select_, from_=table, limit=limit_, offset=offset_)
            (rows,) = self.interface.select(what="count(*) ", from_=table)[0][0]
            return {"contents": data, "rows": rows}

        self.run_parallel_task(
            method=get_table_data,
            method_kwargs={"table": name, "offset_": offset, "limit_": limit, "select_": select},
            at_end=self.sql_filling_table,
            extra_data={"name": name},
        )

    def sql_run_raw_sql(self, tab_name: str, request: str):
        self.run_parallel_task(
            self.interface.raw,
            method_args=(request,),
            at_end=self.sql_filling_table,
            extra_data={"name": tab_name},
        )

    @core.pyqtSlot(object)
    def sql_filling_table(self, data: dict):
        table_name = data.get("name")
        contents = data.get("data")

        self.fillup_table(table_name, contents)

    # endregion
