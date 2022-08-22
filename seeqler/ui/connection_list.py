import PyQt6.QtCore as core
import PyQt6.QtGui as gui
import PyQt6.QtWidgets as widget

from .custom import QLineEdit
from ..common.connection_manager import Connection, ConnectionManager


class ConnectionItem(widget.QWidget):
    """
    Connection list element.
    """

    def __init__(self, parent: "ConnectionListWindow", name: str, uuid: str):
        super().__init__()

        self.daddy = parent  # ( ͡° ͜ʖ ͡°)
        self.settings = parent.settings
        self.uuid = uuid

        self.button_connect = gui.QAction(self.settings.lang.cl_btn_connect)
        self.button_connect.triggered.connect(self.connect)
        self.button_edit = gui.QAction(self.settings.lang.cl_btn_edit)
        self.button_edit.triggered.connect(self.edit)
        self.button_delete = gui.QAction(self.settings.lang.cl_btn_delete)
        self.button_delete.triggered.connect(self.delete)

        menu = widget.QMenu()
        menu.addAction(self.button_connect)
        menu.addAction(self.button_edit)
        menu.addAction(self.button_delete)

        self.menu_button = widget.QPushButton(self.settings.lang.cl_menu_text)
        self.menu_button.setMenu(menu)

        layout = widget.QHBoxLayout()
        layout.addWidget(widget.QLabel(name))
        layout.addWidget(self.menu_button)
        layout.setStretch(0, 3)

        self.setLayout(layout)


    def _get_connection(self):
        return ConnectionManager().get(uuid=self.uuid)

    def connect(self):
        connection = self._get_connection()
        self.settings.connection = connection
        self.daddy.main_window.windows.schema_window.set_up(connection=connection)
        self.daddy.main_window.windows.schema_window.show()
        self.daddy.hide()

    def edit(self):
        connection = self._get_connection()
        self.daddy.open_new_item_dialog(name=connection.label, connection=connection.connection_string, edit=True)

    def delete(self):
        ConnectionManager().remove(self._get_connection())

        if widget := getattr(self, "widget", None):
            self.daddy.conn_list.takeItem(self.daddy.conn_list.row(widget))
        del self

    def mouseReleaseEvent(self, event):
        match event.button():
            case core.Qt.MouseButton.RightButton:
                self.menu_button.click()

    def mouseDoubleClickEvent(self, event):
        match event.button():
            case core.Qt.MouseButton.LeftButton:
                self.connect()


class NewConnection(widget.QDialog):
    """
    New connection creation dialog window.
    """

    def __init__(self, parent: "ConnectionListWindow"):
        super().__init__()

        self.daddy = parent
        self.settings = parent.settings

        self.setWindowTitle(self.settings.lang.cl_win_title_create)
        self.setWindowModality(core.Qt.WindowModality.ApplicationModal)
        self.resize(core.QSize(300, 180))

        self.conn_name = QLineEdit()
        self.conn_string = QLineEdit()

        self.button_add = widget.QPushButton(self.settings.lang.cl_btn_create)
        self.button_add.clicked.connect(self.add_new_item)
        self.button_cancel = widget.QPushButton(self.settings.lang.cl_btn_close)
        self.button_cancel.clicked.connect(self.hide_window)
        self.button_opendialog = widget.QPushButton(self.settings.lang.cl_menu_text)
        self.button_opendialog.clicked.connect(self.open_window)
        self.button_opendialog.setMaximumSize(core.QSize(30, 50))

        button_layout = widget.QHBoxLayout()
        button_layout.addWidget(self.button_add)
        button_layout.addWidget(self.button_cancel)
        button_layout.setSpacing(30)

        name_layout = widget.QVBoxLayout()
        name_layout.addWidget(widget.QLabel(self.settings.lang.cl_lbl_connection_label))
        name_layout.addWidget(self.conn_name)

        open_layout = widget.QHBoxLayout()
        open_layout.addWidget(self.conn_string)
        open_layout.addWidget(self.button_opendialog)

        string_layout = widget.QVBoxLayout()
        string_layout.addWidget(widget.QLabel(self.settings.lang.cl_lbl_connection_string))
        string_layout.addLayout(open_layout)

        layout = widget.QVBoxLayout()
        layout.addLayout(name_layout)
        layout.addStretch(1)
        layout.addLayout(string_layout)
        layout.addStretch(1)
        # layout.addSpacing(15)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def fill(self, name: str = "", connection: str = "", edit: bool = False):
        self.conn_name.setText(name)
        self.conn_string.setText(connection)
        self.button_add.setText(self.settings.lang.cl_btn_save if edit else self.settings.lang.cl_btn_create)

    def add_new_item(self):
        label, connection = self.conn_name.text(), self.conn_string.text()

        if not label or not connection:
            if not label:
                self.conn_name.makeError(placeholder=self.settings.lang.cl_lbl_connection_label_error)
            if not connection:
                self.conn_string.makeError(placeholder=self.settings.lang.cl_lbl_connection_string_error)
            return

        conn = Connection(label, connection)
        ConnectionManager().add(conn)
        self.daddy.add_new_item(label, conn.uuid)
        self.hide_window()

    def clear(self):
        self.conn_name.clear()
        self.conn_name.keyPressed.emit(0)
        self.conn_string.clear()
        self.conn_string.keyPressed.emit(0)

    def closeEvent(self, event) -> None:
        self.clear()
        super().closeEvent(event)

    def hide_window(self):
        self.clear()
        self.hide()

    def open_window(self):
        filename, _ = widget.QFileDialog.getOpenFileName(self, self.settings.lang.cl_opendialog_title, "")
        if filename:
            # TODO: update connection string format
            self.conn_string.setText("sqlite:///" + filename)


class ConnectionListWindow(widget.QWidget):
    def __init__(self, main_window, settings):
        super().__init__()

        self.main_window = main_window
        self.settings = settings

        self.setWindowTitle(self.settings.lang.cl_win_title_main)
        self.setFixedSize(core.QSize(500, 400))

        label = widget.QLabel(self.settings.lang.cl_lbl_saved_connections)
        self.conn_list = widget.QListWidget()
        button = widget.QPushButton(self.settings.lang.cl_btn_create_connection)
        button.clicked.connect(self.open_new_item_dialog)

        layout = widget.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.conn_list)
        layout.addWidget(button)
        self.setLayout(layout)

        self.new_conn_dialog = NewConnection(self)
        self.fill_from_manager()

    def add_new_item(self, name: str, uuid):
        item = ConnectionItem(self, name, uuid)
        list_item = widget.QListWidgetItem(self.conn_list)
        list_item.setSizeHint(item.minimumSizeHint())
        self.conn_list.setItemWidget(list_item, item)

        item.widget = list_item

    def fill_from_manager(self):
        for conn in ConnectionManager():
            self.add_new_item(conn.label, conn.uuid)

    def open_new_item_dialog(self, *, name: str = "", connection: str = "", edit: bool = False):
        self.new_conn_dialog.fill(name=name, connection=connection, edit=edit)
        self.new_conn_dialog.show()
