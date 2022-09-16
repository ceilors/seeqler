from pathlib import Path

from .common.connection_manager import Connection, ConnectionManager
from .common.language import Language
from .settings import Settings
from .ui.app import get_app

RESOURCES_PATH = Path(__file__).parents[1] / "resources"
LANGUAGE = "RU-RU"  # TODO: replace with preferences


class Seeqler:
    def __init__(self, connection_string: str | None = None):
        self.settings = Settings(Language(LANGUAGE), RESOURCES_PATH)

        if connection_string:
            try:
                self.settings.connection = ConnectionManager().get(connection_string=connection_string)
            except (ValueError, AttributeError):
                # temp connection
                name = self.settings.lang.app_win_title_temp
                self.settings.connection = Connection(name, connection_string)

    def run(self):
        app, main_window = get_app(self.settings)
        app.exec()
