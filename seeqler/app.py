from pathlib import Path

from .common.types import Descriptor
from .ui.language import Language
from .ui.main import get_app


RESOURCES_PATH = Path(__file__).parents[1] / "resources"
LANGUAGE = "RU-RU"  # TODO: replace with preferences


class Seeqler:
    def __init__(self, connection_string: str | None = None):
        self.settings = Descriptor()
        self.settings.lang = Language(LANGUAGE)
        self.settings.resources_path = RESOURCES_PATH
        self.settings.connection = None

        if connection_string:
            self.settings.connection = connection_string

    def run(self):
        app, main_window = get_app(self.settings)
        app.exec()
