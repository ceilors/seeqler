from pathlib import Path
from typing import Optional

import sqlalchemy as sa
import dearpygui.dearpygui as dpg

from .ui import SchemaWindow, ConnectionListWindow, TAG_DEFAULT_FONT


RESOURCES_PATH = Path(__file__).parent.parent / 'resources'


class Seeqler:
    def init(self, connection_string: str):
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)

    def __init__(self, connection_string: Optional[str] = None):
        if connection_string:
            self.init(connection_string)

    def run(self):
        dpg.create_context()

        # create font once for all the app windows
        with dpg.font_registry(), dpg.font(RESOURCES_PATH / 'FiraMono-Regular.ttf', 16, tag=TAG_DEFAULT_FONT):
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x2000, 0x206F)  # general punctuation
            dpg.add_font_range(0x2190, 0x21FF)  # arrows

        dpg.create_viewport(title='Seeqler', width=800, height=500)

        if hasattr(self, "inspector"):
            SchemaWindow(self.inspector, self.engine).show()
        else:
            ConnectionListWindow().show()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
