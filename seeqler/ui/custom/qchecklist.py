from PyQt6 import QtCore as core, QtGui as gui, QtWidgets as widget


class QCheckList(widget.QWidget):
    def __init__(
        self, items: list[tuple[bool, str]], show_header: str | None = None, movable: bool = False, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.listview = QCheckListView(self, items, movable)
        layout = widget.QVBoxLayout()

        if show_header is not None:
            self.checkbox = widget.QCheckBox(show_header)
            self.updateCheckboxValue()
            self.checkbox.clicked.connect(self.listview.model().checkAll)
            layout.addWidget(self.checkbox)

        layout.addWidget(self.listview)
        self.setLayout(layout)

    def updateCheckboxValue(self):
        if not hasattr(self, "checkbox"):
            return

        model: "CheckableModel" = self.listview.model()

        state, row_count = 0, model.rowCount()
        for row in range(row_count):
            state += int(model.item(row, 0).checkState() == core.Qt.CheckState.Checked)
        self.checkbox.setCheckState(
            core.Qt.CheckState.Unchecked
            if state == 0
            else core.Qt.CheckState.Checked
            if state == row_count
            else core.Qt.CheckState.PartiallyChecked
        )

    def getValue(self):
        return self.listview.getValue()


class CheckableModel(gui.QStandardItemModel):
    def __init__(self, listview: "QCheckListView", items: list[tuple[bool, str]], movable: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setParent(listview)

        for checked, text in items:
            item = gui.QStandardItem(text)
            item.setCheckable(True)
            item.setCheckState(core.Qt.CheckState.Checked if checked else core.Qt.CheckState.Unchecked)
            self.appendRow(item)

    def checkAll(self, value):
        for row in range(self.rowCount()):
            self.item(row, 0).setCheckState(core.Qt.CheckState.Checked if value else core.Qt.CheckState.Unchecked)


class QCheckListView(widget.QListView):
    def __init__(self, parent: "QCheckList", items: list[tuple[bool, str]], movable: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setParent(parent)

        self.setModel(CheckableModel(self, items, movable))
        self.model().itemChanged.connect(self.emitUpdateCheckbox)

    def emitUpdateCheckbox(self, item: gui.QStandardItem):
        self.parent().updateCheckboxValue()

    def getValue(self):
        table: CheckableModel = self.model()
        result = []

        while table.rowCount():
            row = table.takeRow(0)
            result.append((row[0].checkState() == core.Qt.CheckState.Checked, row[0].text()))
        return result