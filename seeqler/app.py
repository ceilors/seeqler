from pathlib import Path

from .common.types import Descriptor
from .ui.language import Language
from .ui.app import get_app


RESOURCES_PATH = Path(__file__).parents[1] / "resources"
LANGUAGE = "RU-RU"  # TODO: replace with preferences


class Seeqler:
    def __init__(self, connection_string: str | None = None):
        self.settings = Descriptor()
        self.settings.lang = Language(LANGUAGE)
        self.settings.resources_path = RESOURCES_PATH
        self.settings.rows_per_page = 100
        self.settings.connection = None

        if connection_string:
            from .common.connection_manager import Connection, ConnectionManager

            try:
                self.settings.connection = ConnectionManager().get(connection_string=connection_string)
            except (ValueError, AttributeError):
                # temp connection
                name = self.settings.lang.app_win_title_temp
                self.settings.connection = Connection(name, connection_string)

    def run(self):
        app, main_window = get_app(self.settings)
        app.exec()
