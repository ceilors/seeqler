from types import SimpleNamespace

import PyQt6.QtWidgets as widget
from PyQt6.QtGui import QFontDatabase

from .connection_list import ConnectionListWindow
from .schema import SchemaWindow


class MainWindow(widget.QMainWindow):
    def __init__(self, settings):
        super().__init__()

        self.windows = SimpleNamespace()
        self.windows.connection_manager = ConnectionListWindow(self, settings)
        self.windows.schema_window = SchemaWindow(self)

        if settings.connection:
            self.windows.schema_window.set_up(settings.connection)
            self.windows.schema_window.show()
        else:
            self.windows.connection_manager.show()


def get_app(settings):
    app = widget.QApplication([])

    # load all needed fonts
    for font in settings.font_list:
        QFontDatabase.addApplicationFont(str(settings.resources_path / font))

    with open(settings.resources_path / "app_style.qss", "r") as qss:
        app.setStyleSheet(qss.read())

    screen_size = app.primaryScreen().size()
    settings.screen_width, settings.screen_height = screen_size.width(), screen_size.height()

    window = MainWindow(settings)

    return app, window
