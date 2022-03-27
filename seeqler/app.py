from pathlib import Path

import sqlalchemy as sa
import toga

from seeqler.ui.language import Language

from .ui import ConnectionListWindow, SchemaWindow


RESOURCES_PATH = Path(__file__).parents[1] / "resources"
LANGUAGE = "RU-RU"  # TODO: replace with preferences


class UIApp(toga.App):
    def __init__(self, seeqler: "Seeqler", *args, **kwargs):
        self.seeqler = seeqler
        super().__init__(*args, **kwargs)

    def startup(self):
        toga.fonts.Font.register("Fira Mono", RESOURCES_PATH / "FiraMono-Regular.ttf")
        self.default_style = toga.style.Pack(font_family="Fira Mono", font_size=10)

        self.commands = toga.CommandSet(None)
        # TODO: check if works on macOS
        # if toga.platform.current_platform != "darwin":
        self._impl.create_menus = lambda *x, **y: None

        if self.seeqler.has_connection:
            window = SchemaWindow(app=self)
        else:
            window = ConnectionListWindow(app=self)

        self.main_window = window.get_window()
        window.show()


class Seeqler:
    def __init__(self, connection_string: str | None = None):
        self.lang = Language(LANGUAGE)

        if connection_string:
            self.connect(connection_string)

    def connect(self, connection_string: str):
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)

    @property
    def has_connection(self) -> bool:
        return hasattr(self, "inspector")

    def run(self) -> toga.App:
        app = UIApp(self, self.lang.app_name, "org.ceilors.seeqler")
        return app
