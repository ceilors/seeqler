from PyQt6.QtGui import QFontDatabase
import PyQt6.QtWidgets as widget

from ..common.types import Descriptor
from .connection_list import ConnectionListWindow

# from .schema import SchemaWindow


class MainWindow(widget.QMainWindow):
    def __init__(self, settings):
        super().__init__()

        self.windows = Descriptor()
        self.windows.connection_manager = ConnectionListWindow(settings)

        self.windows.connection_manager.show()


def get_app(settings):
    app = widget.QApplication([])

    # using FiraMono for whole app
    font_id = QFontDatabase.addApplicationFont(str(settings.resources_path / "FiraMono-Regular.ttf"))
    if font_id >= 0:
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setStyleSheet(f'* {{ font-family: "{font_name}"; }}')

    window = MainWindow(settings)

    return app, window
