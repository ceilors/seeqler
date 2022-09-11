from typing import TYPE_CHECKING, Any

from PyQt6 import QtCore as core, QtGui as gui, QtWidgets as widget

from seeqler.common.language import Language
from seeqler.settings import Settings

from .checklist import CheckList
from .utils import retain_place

if TYPE_CHECKING:
    from ..schema import SchemaWindow


DEFAULT_ROW_COUNT = 5  # default row count until table is filled up
STATUSBAR_HEIGHT = 25  # SeeqlerTab bottom_layout QSpacerItem height


class TabInputDialog(widget.QInputDialog):
    @staticmethod
    def getInteger(parent: widget.QWidget, value: int = 0, min: int = 1, max: int = 2**31 - 1) -> tuple[int, bool]:
        lang = Language()

        inp = TabInputDialog(parent)
        inp.setInputMode(TabInputDialog.InputMode.IntInput)
        inp.setFixedSize(400, 200)

        inp.setWindowTitle(lang.qst_inp_edit_limit)
        inp.setLabelText(lang.qst_lbl_edit_limit)
        inp.setIntMinimum(min)
        inp.setIntMaximum(max)
        inp.setIntValue(value)
        inp.setIntStep(1)

        inp.setOkButtonText(lang.qst_inp_ok)
        inp.setCancelButtonText(lang.qst_inp_cancel)

        if inp.exec() == TabInputDialog.DialogCode.Accepted:
            result = (inp.intValue(), True)
        else:
            result = (value, False)

        inp.deleteLater()
        return result

    @staticmethod
    def getColumns(parent: widget.QWidget, value: list[tuple[bool, str]]) -> list[tuple[bool, str]]:
        dialog = TabInputDialog().ColumnDialog(parent, value)
        if dialog.exec() == TabInputDialog.DialogCode.Accepted:
            result = (dialog.getColumnValue(), True)
        else:
            result = (value, False)

        dialog.deleteLater()
        return result

    def ColumnDialog(self, parent: widget.QWidget, value: list[tuple[bool, str]]) -> widget.QDialog:
        lang = Language()

        inp = widget.QDialog(parent)
        inp.setParent(parent)
        inp.setWindowTitle(lang.qst_inp_edit_columns)
        inp.setFixedSize(400, 500)

        label = widget.QLabel(lang.qst_lbl_edit_columns)
        table = CheckList(value, show_header=lang.qst_hdr_edit_columns, movable=True)

        setattr(inp, "getColumnValue", lambda: table.getValue())

        input_layout = widget.QVBoxLayout()
        input_layout.addWidget(label)
        input_layout.addWidget(table)

        ok_btn = widget.QPushButton(lang.qst_inp_ok)
        ok_btn.clicked.connect(inp.accept)
        cancel_btn = widget.QPushButton(lang.qst_inp_cancel)
        cancel_btn.clicked.connect(inp.reject)

        btn_layout = widget.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout = widget.QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(btn_layout)

        inp.setLayout(layout)
        return inp


class PagedTable(widget.QWidget):
    onRequestedUpdate = core.pyqtSignal()

    def __init__(self, parent, offset: int, limit: int, columns: list[dict], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.lang = Language()

        self.default_columns = [x["name"] for x in columns]
        self.offset = offset
        self.limit = limit

        self.table = widget.QTableWidget()
        self.update_cols([x["name"] for x in columns])

        self.bottom_layout = widget.QHBoxLayout()

        self.statusbar = widget.QLabel()
        self.statusbar.setText(f"1-? {self.lang.qst_statusbar_of} ?")
        self.statusbar.setAlignment(core.Qt.AlignmentFlag.AlignCenter)
        self.statusbar.setSizePolicy(retain_place)

        self.btn_left = widget.QPushButton()
        self.btn_left.setText(self.lang.qst_statusbar_left)
        self.btn_left.clicked.connect(lambda: self.change_table_page(-1))
        self.btn_left.setDisabled(True)
        self.btn_left.setSizePolicy(retain_place)

        self.btn_right = widget.QPushButton()
        self.btn_right.setText(self.lang.qst_statusbar_right)
        self.btn_right.clicked.connect(lambda: self.change_table_page(1))
        self.btn_right.setDisabled(True)
        self.btn_right.setSizePolicy(retain_place)

        self.edit_config = widget.QPushButton(self.lang.qst_btn_config)
        self.edit_config.setSizePolicy(retain_place)

        menu = widget.QMenu()

        edit_columns = gui.QAction(self.lang.qst_btn_edit_columns, menu)
        edit_columns.triggered.connect(self.config_menu_change_columns)
        edit_limit = gui.QAction(self.lang.qst_btn_edit_limit, menu)
        edit_limit.triggered.connect(self.config_menu_change_limit)

        menu.addAction(edit_columns)
        menu.addAction(edit_limit)

        self.edit_config.setMenu(menu)

        self.bottom_layout.addWidget(self.statusbar, alignment=core.Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout.insertWidget(0, self.btn_left, alignment=core.Qt.AlignmentFlag.AlignLeft)
        self.bottom_layout.addWidget(self.btn_right, alignment=core.Qt.AlignmentFlag.AlignRight)
        self.bottom_layout.addWidget(self.edit_config)
        self.bottom_layout.addSpacerItem(widget.QSpacerItem(0, 25, hPolicy=widget.QSizePolicy.Policy.Ignored))

        self.general_layout = widget.QVBoxLayout()
        self.general_layout.setContentsMargins(0, 0, 0, 0)
        self.general_layout.addWidget(self.table)
        self.general_layout.addLayout(self.bottom_layout)
        self.setLayout(self.general_layout)

    def prepare_table(self):
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setRowCount(0)
        self.table.setRowCount(DEFAULT_ROW_COUNT)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setStretchLastSection(False)
        self.table.setWordWrap(False)

    def update_cols(self, columns: list[str]):
        self.columns = columns
        self.prepare_table()

    def get_column_names(self):
        return [(x in self.columns, x) for x in self.default_columns]

    def get_sql_select(self):
        if not self.columns:
            return "''"
        if self.columns == self.default_columns:
            return "*"
        return ", ".join(f'"{x}"' for x in self.columns)

    def change_table_page(self, sign: int):
        self.offset += sign * self.limit
        self.onRequestedUpdate.emit()

    def config_menu_change_columns(self):
        value, ok = TabInputDialog.getColumns(self, value=self.get_column_names())
        if ok:
            self.columns = [x[1] for x in value if x[0]]
            self.prepare_table()
            self.onRequestedUpdate.emit()

    def config_menu_change_limit(self):
        value, ok = TabInputDialog.getInteger(self, value=self.limit)
        if ok:
            self.limit = value
            self.onRequestedUpdate.emit()

    def fillup_table(self, data: dict[str, int | list[Any]]):
        contents = data["contents"]
        row_number = data["rows"]
        table_rows = len(contents)
        current_rows = self.offset + table_rows

        self.table.setRowCount(table_rows)
        self.table.scrollToTop()

        for row, data_row in enumerate(contents):
            for col, cell in enumerate(data_row):
                content = widget.QTableWidgetItem(str(cell))
                self.table.setItem(row, col, content)

        methods = {True: "setEnabled", False: "setDisabled"}

        getattr(self.btn_left, methods[self.offset >= self.limit])(True)
        getattr(self.btn_right, methods[current_rows != row_number])(True)

        self.statusbar.setText(f"{self.offset + 1}-{current_rows} {self.lang.qst_statusbar_of} {row_number}")

        if row_number == 0:
            self.statusbar.setText(f"0 {self.lang.qst_statusbar_of} 0")

    def focus(self):
        self.table.setFocus()


class PagedTableWithMeta(PagedTable):
    def __init__(self, parent, offset: int, limit: int, columns: list[dict], *args, **kwargs):
        super().__init__(parent, offset, limit, columns)

        headers = ["parameter", "type", "nullable", "default value", "foreign key"]
        self.meta_table = widget.QTableWidget()
        self.meta_table.setColumnCount(len(headers))
        self.meta_table.setHorizontalHeaderLabels(headers)
        self.meta_table.setRowCount(len(columns))
        self.meta_table.setHidden(True)

        for row, item in enumerate(columns):
            for col, key in enumerate(("name", "type", "nullable", "default", "fkey")):
                self.meta_table.setItem(row, col, widget.QTableWidgetItem(str(item[key])))

        config_layout = widget.QHBoxLayout()

        self.show_data = widget.QPushButton()
        self.show_data.setText(self.lang.qst_switchview_data)
        self.show_data.setProperty("class", "swButtonSwitch")
        self.show_data.setDisabled(True)
        self.show_data.clicked.connect(lambda: self.switch_meta_info(False))
        self.show_data.setSizePolicy(retain_place)

        self.show_meta = widget.QPushButton()
        self.show_meta.setText(self.lang.qst_switchview_meta)
        self.show_meta.setProperty("class", "swButtonSwitch")
        self.show_meta.clicked.connect(lambda: self.switch_meta_info(True))
        self.show_meta.setSizePolicy(retain_place)

        config_layout.addWidget(self.show_data)
        config_layout.addWidget(self.show_meta)

        self.bottom_layout.addLayout(config_layout)
        self.general_layout.insertWidget(1, self.meta_table)

    def switch_meta_info(self, show_meta: bool = True):
        self.table.setHidden(show_meta)
        self.show_data.setEnabled(show_meta)
        self.meta_table.setVisible(show_meta)
        self.show_meta.setDisabled(show_meta)
        self.statusbar.setHidden(show_meta)
        self.btn_left.setHidden(show_meta)
        self.btn_right.setHidden(show_meta)
        self.edit_config.setHidden(show_meta)


class PagedTableWithEditor(PagedTable):
    def __init__(self, parent, offset, limit, columns, *args, **kwargs):
        super().__init__(parent, offset, limit, columns, *args, **kwargs)

        self.textarea = widget.QTextEdit(self)
        self.general_layout.insertWidget(0, self.textarea)

        self.label_result = widget.QLabel(self)
        self.label_result.hide()
        self.general_layout.insertWidget(2, self.label_result)

        self.run = widget.QPushButton(self.lang.qst_tab_raw_run)
        self.run.setSizePolicy(retain_place)
        self.run.clicked.connect(self.execute)
        self.bottom_layout.addWidget(self.run)

    def update_cols(self, columns: list[str]):
        self.default_columns = columns
        super().update_cols(columns)

    def execute(self):
        self.label_result.hide()
        self.table.show()
        self.prepare_table()
        self.onRequestedUpdate.emit()

    def fillup_table(self, data: tuple[dict[str, int | list[Any]], list[str]]):
        data, columns = data

        if isinstance(columns, str):
            self.table.hide()
            self.label_result.show()
            text = str(data)
            if columns == "error":
                text = f"{self.lang.qst_tab_raw_col_error}\n\n{data}"
            if columns == "norows":
                text = f"{self.lang.qst_tab_raw_col_result}\n\n{self.lang.qst_tab_raw_matched_rows.format(rows=data)}"
            self.label_result.setText(text)
            return

        table_rows = len(data)
        data = data[self.offset : self.offset + self.limit]
        self.update_cols([x for x in columns])
        super().fillup_table({"contents": data, "rows": table_rows})

    def focus(self):
        self.textarea.focusInEvent(gui.QFocusEvent(core.QEvent.Type.FocusIn))
        self.textarea.setFocus()


class SeeqlerTab(widget.QWidget):
    def __init__(
        self, parent: "SchemaWindow", table_name: str, columns: list[dict] = None, raw: bool = False, *args, **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.daddy = parent
        self.settings = Settings()
        self.table_name = table_name
        self.raw = raw

        self.general_layout = widget.QVBoxLayout()

        getattr(self, f"init_ui_{'raw' if self.raw else 'normal'}")(columns)

        self.setLayout(self.general_layout)

    def init_ui_raw(self, _):
        self.paged_table = PagedTableWithEditor(self, 0, self.settings.rows_per_page, [])
        self.paged_table.onRequestedUpdate.connect(self.load_table_contents)
        self.general_layout.addWidget(self.paged_table)

    def init_ui_normal(self, columns):
        self.paged_table = PagedTableWithMeta(self, 0, self.settings.rows_per_page, columns)
        self.paged_table.onRequestedUpdate.connect(self.load_table_contents)
        self.general_layout.addWidget(self.paged_table)

    def focus(self):
        self.paged_table.focus()

    def load_table_contents(self):
        if self.raw:
            self.daddy.sql_run_raw_sql(self.table_name, self.paged_table.textarea.toPlainText())
        else:
            self.daddy.sql_get_table_contents(
                self.table_name, self.paged_table.offset, self.paged_table.limit, self.paged_table.get_sql_select()
            )

    def fillup_table(self, data):
        # this method is called from sql_get_table_contents' after
        return self.paged_table.fillup_table(data)
