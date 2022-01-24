from pathlib import Path
from typing import Optional

import sqlalchemy as sa
import dearpygui.dearpygui as dpg

from .ui_windows import create_connection_list_window, create_connection_schema_window


class Seeqler:
    tag_schema_selector = 'schema selector'
    tag_listbox = 'table list'
    tag_content = 'current table'
    tag_schema = 'current schema'
    tag_handler = 'table list handler'
    tag_limit = 'select_limit'
    tag_default_font = 'default font'
    id_window = 'main_window'
    id_list_window = 'connection_list'
    # fmt: off
    table_params = {
        'header_row': True, 'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True,
        'borders_outerV': True, 'resizable': True, 'no_host_extendX': True
    }
    # fmt: on

    def init(self, connection_string: str):
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)

    def __init__(self, connection_string: Optional[str] = None):
        if connection_string:
            self.init(connection_string)

    def ui_select_table(self, sender, table=None):
        dpg.delete_item(self.tag_content, children_only=True)
        dpg.delete_item(self.tag_schema, children_only=True)

        schema = dpg.get_value(self.tag_schema_selector)
        table = table or dpg.get_value(self.tag_listbox)
        limit = dpg.get_value(self.tag_limit)

        if not table:
            return

        columns = self.inspector.get_columns(table, schema=schema)
        for c in columns:
            dpg.add_table_column(label=c['name'], parent=self.tag_content)
        for column in ['param', 'type', 'nullable', 'default', 'foreign key']:
            dpg.add_table_column(label=column, parent=self.tag_schema)

        with self.engine.connect() as conn:
            for row in conn.execute(f'select * from {table} limit {limit}'):
                with dpg.table_row(parent=self.tag_content):
                    for e in row:
                        dpg.add_text(e)

            foreign_keys = {
                i['constrained_columns'][0]: '{referred_schema}.{referred_table}({referred_columns[0]})'.format(**i)
                for i in self.inspector.get_foreign_keys(table, schema=schema)
            }
            for item in columns:
                with dpg.table_row(parent=self.tag_schema):
                    dpg.add_text(item['name'])
                    dpg.add_text(item['type'])
                    dpg.add_text(item['nullable'])
                    dpg.add_text(item['default'])
                    dpg.add_text(foreign_keys.get(item['name']))

    def ui_select_schema(self, sender, schema):
        dpg.configure_item(self.tag_listbox, items=sorted(self.inspector.get_table_names(schema=schema)))
        self.ui_select_table(sender)  # because listbox has selected item, but doesnt trigger callback itself

    def run(self):
        schemas = self.inspector.get_schema_names()
        dpg.create_context()

        with dpg.font_registry():
            with dpg.font(Path(__file__).parent.parent / 'resources'/ 'FiraMono-Regular.ttf', 16, tag=self.tag_default_font) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

        dpg.create_viewport(title='Seeqler', width=800, height=500)

        create_connection_list_window(self, window_id=self.id_list_window)
        dpg.set_primary_window(self.id_list_window, True)

        if hasattr(self, "inspector"):
            create_connection_schema_window(self, schemas=self.inspector.get_schema_names(), window_id=self.id_window)
            dpg.set_viewport_width(800)
            dpg.set_viewport_height(500)
            dpg.set_primary_window(self.id_window, True)

        dpg.set_primary_window(self.id_window, True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
