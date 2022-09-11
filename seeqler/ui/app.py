from PyQt6.QtGui import QFontDatabase
import PyQt6.QtWidgets as widget

from .connection_list import ConnectionListWindow
from .schema import SchemaWindow

from types import SimpleNamespace


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

    # using FiraMono for whole app
    font_id = QFontDatabase.addApplicationFont(str(settings.resources_path / "FiraMono-Regular.ttf"))
    if font_id >= 0:
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
    with open(settings.resources_path / "app_style.qss", "r") as qss:
        app.setStyleSheet(qss.read())

    screen_size = app.primaryScreen().size()
    settings.screen_width, settings.screen_height = screen_size.width(), screen_size.height()

    window = MainWindow(settings)

    return app, window
