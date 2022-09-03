from typing import TYPE_CHECKING, Any

from PyQt6 import QtCore as core, QtGui as gui, QtWidgets as widget

from .qchecklist import QCheckList

if TYPE_CHECKING:
    from ..schema import SchemaWindow


DEFAULT_ROW_COUNT = 5  # default row count until table is filled up
STATUSBAR_HEIGHT = 25  # QSeeqlerTab bottom_layout QSpacerItem height


class TabConfig:
    def __init__(self, table_name: str, offset: int, limit: int, columns: list[str]):
        self.table_name = table_name
        self.offset = offset
        self.limit = limit
        self.columns_default = columns
        self.columns = columns

    def get_column_items(self):
        return [(x in self.columns, x) for x in self.columns_default]

    def get_select(self):
        if self.columns == self.columns_default:
            return "*"
        if not self.columns:
            return "''"
        return ", ".join(f'"{x}"' for x in self.columns)


class TabInputDialog(widget.QInputDialog):
    @staticmethod
    def getInteger(
        parent: widget.QWidget, lang, value: int = 0, min: int = 1, max: int = 2**31 - 1
    ) -> tuple[int, bool]:
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
    def getColumns(parent: widget.QWidget, lang, value: list[tuple[bool, str]]) -> list[tuple[bool, str]]:
        dialog = TabInputDialog().ColumnDialog(parent, lang, value)
        if dialog.exec() == TabInputDialog.DialogCode.Accepted:
            result = (dialog.getColumnValue(), True)
        else:
            result = (value, False)

        dialog.deleteLater()
        return result

    def ColumnDialog(self, parent: widget.QWidget, lang, value: list[tuple[bool, str]]) -> widget.QDialog:
        inp = widget.QDialog(parent)
        inp.setParent(parent)
        inp.setWindowTitle(lang.qst_inp_edit_columns)
        inp.setFixedSize(400, 500)

        label = widget.QLabel(lang.qst_lbl_edit_columns)
        table = QCheckList(value, show_header=lang.qst_hdr_edit_columns, movable=True)

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


class QSeeqlerTab(widget.QWidget):
    def __init__(self, table_name: str, columns: list[dict], parent_window: "SchemaWindow", *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = widget.QVBoxLayout()
        self.daddy = parent_window
        self.settings = self.daddy.settings

        self.config = TabConfig(table_name, 0, self.settings.rows_per_page, [x["name"] for x in columns])

        self.table = widget.QTableWidget()
        self.prepare_table()
        self.table.setWordWrap(False)

        retain_place = widget.QSizePolicy()
        retain_place.setRetainSizeWhenHidden(True)

        # ----

        bottom_layout = widget.QHBoxLayout()

        self.statusbar = widget.QLabel()
        self.statusbar.setText(f"1-? {self.settings.lang.qst_statusbar_of} ?")
        self.statusbar.setAlignment(core.Qt.AlignmentFlag.AlignCenter)
        self.statusbar.setSizePolicy(retain_place)

        self.btn_left = widget.QPushButton()
        self.btn_left.setText(self.settings.lang.qst_statusbar_left)
        self.btn_left.clicked.connect(lambda: self.change_table_page(-1))
        self.btn_left.setDisabled(True)
        self.btn_left.setSizePolicy(retain_place)

        self.btn_right = widget.QPushButton()
        self.btn_right.setText(self.settings.lang.qst_statusbar_right)
        self.btn_right.clicked.connect(lambda: self.change_table_page(1))
        self.btn_right.setDisabled(True)
        self.btn_right.setSizePolicy(retain_place)

        bottom_layout.addWidget(self.statusbar, alignment=core.Qt.AlignmentFlag.AlignCenter)
        bottom_layout.insertWidget(0, self.btn_left, alignment=core.Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(self.btn_right, alignment=core.Qt.AlignmentFlag.AlignRight)

        # ----

        headers = [
            self.settings.lang.qst_meta_table_param,
            self.settings.lang.qst_meta_table_type,
            self.settings.lang.qst_meta_table_nullable,
            self.settings.lang.qst_meta_table_default,
            self.settings.lang.qst_meta_table_fkey,
        ]
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
        self.show_data.setText(self.settings.lang.qst_switchview_data)
        self.show_data.setProperty("class", "swButtonSwitch")
        self.show_data.setDisabled(True)
        self.show_data.clicked.connect(lambda: self.switch_meta_info(False))
        self.show_data.setSizePolicy(retain_place)

        self.show_meta = widget.QPushButton()
        self.show_meta.setText(self.settings.lang.qst_switchview_meta)
        self.show_meta.setProperty("class", "swButtonSwitch")
        self.show_meta.clicked.connect(lambda: self.switch_meta_info(True))
        self.show_meta.setSizePolicy(retain_place)

        self.edit_config = widget.QPushButton(self.settings.lang.qst_btn_config)
        self.edit_config.setSizePolicy(retain_place)

        menu = widget.QMenu()

        edit_columns = gui.QAction(self.settings.lang.qst_btn_edit_columns, menu)
        edit_columns.triggered.connect(self.config_menu_change_columns)
        edit_limit = gui.QAction(self.settings.lang.qst_btn_edit_limit, menu)
        edit_limit.triggered.connect(self.config_menu_change_limit)

        menu.addAction(edit_columns)
        menu.addAction(edit_limit)

        self.edit_config.setMenu(menu)

        config_layout.addWidget(self.edit_config)
        config_layout.addWidget(self.show_data)
        config_layout.addWidget(self.show_meta)

        bottom_layout.addLayout(config_layout)
        bottom_layout.addSpacerItem(widget.QSpacerItem(0, 25, hPolicy=widget.QSizePolicy.Policy.Ignored))

        # ----

        layout.addWidget(self.table)
        layout.addWidget(self.meta_table)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def prepare_table(self):
        self.table.setColumnCount(len(self.config.columns))
        self.table.setHorizontalHeaderLabels(self.config.columns)
        self.table.setRowCount(0)
        self.table.setRowCount(DEFAULT_ROW_COUNT)
        self.table.resizeColumnsToContents()

    def fillup_table(self, data: list[list[Any]]):
        contents = data["contents"]
        row_number = data["rows"]
        table_rows = len(contents)
        current_rows = self.config.offset + table_rows

        self.table.setRowCount(table_rows)
        self.table.scrollToTop()

        for row, data_row in enumerate(contents):
            for col, cell in enumerate(data_row):
                content = widget.QTableWidgetItem(str(cell))
                self.table.setItem(row, col, content)

        methods = {True: "setEnabled", False: "setDisabled"}

        getattr(self.btn_left, methods[self.config.offset >= self.config.limit])(True)
        getattr(self.btn_right, methods[current_rows != row_number])(True)

        self.statusbar.setText(
            f"{self.config.offset + 1}-{current_rows} {self.settings.lang.qst_statusbar_of} {row_number}"
        )

        if row_number == 0:
            self.statusbar.setText(f"0 {self.settings.lang.qst_statusbar_of} 0")

    def change_table_page(self, sign: int):
        self.config.offset += sign * self.config.limit
        self.daddy.sql_get_table_contents(
            self.config.table_name, self.config.offset, self.config.limit, self.config.get_select()
        )

    def switch_meta_info(self, show_meta: bool = True):
        self.table.setHidden(show_meta)
        self.show_data.setEnabled(show_meta)
        self.meta_table.setVisible(show_meta)
        self.show_meta.setDisabled(show_meta)
        self.statusbar.setHidden(show_meta)
        self.btn_left.setHidden(show_meta)
        self.btn_right.setHidden(show_meta)
        self.edit_config.setHidden(show_meta)

    def config_menu_change_columns(self):
        value, ok = TabInputDialog.getColumns(self, self.settings.lang, value=self.config.get_column_items())
        if ok:
            self.config.columns = [x[1] for x in value if x[0]]
            self.prepare_table()
            self.daddy.sql_get_table_contents(
                self.config.table_name, self.config.offset, self.config.limit, self.config.get_select()
            )

    def config_menu_change_limit(self):
        value, ok = TabInputDialog.getInteger(self, self.settings.lang, value=self.config.limit)
        if ok:
            self.config.limit = value
            self.daddy.sql_get_table_contents(
                self.config.table_name, self.config.offset, self.config.limit, self.config.get_select()
            )
