from pathlib import Path

import sqlalchemy as sa
import dearpygui.dearpygui as dpg


class Seeqler:
    tag_schema_selector = 'schema selector'
    tag_listbox = 'table list'
    tag_content = 'current table'
    tag_schema = 'current schema'
    tag_handler = 'table list handler'
    tag_limit = 'select_limit'
    id_window = 'main_window'
    table_params = {
        'header_row': True, 'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True,
        'borders_outerV': True, 'resizable': True, 'no_host_extendX': True
    }

    def __init__(self, connection_string: str) -> 'Seeqler':
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)

    def ui_select_table(self, sender, table=None):
        dpg.delete_item(self.tag_content, children_only=True)
        dpg.delete_item(self.tag_schema, children_only=True)

        schema = dpg.get_value(self.tag_schema_selector)
        table = table or dpg.get_value(self.tag_listbox)
        limit = dpg.get_value(self.tag_limit)

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
        self.ui_select_table(sender) # because listbox has selected item, but doesnt trigger callback itself

    def run(self):
        schemas = self.inspector.get_schema_names()
        dpg.create_context()

        with dpg.font_registry():
            with dpg.font(Path(__file__).parent.parent / 'resources'/ 'FiraMono-Regular.ttf', 16, tag='default font') as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

        with dpg.window(label='Window', id=self.id_window):
            dpg.bind_font('default font')

            with dpg.group(horizontal=True):
                with dpg.group(width=200):
                    dpg.add_text('Schemas')
                    dpg.add_combo(schemas, tag=self.tag_schema_selector, callback=self.ui_select_schema)
                    dpg.add_text('Tables')
                    dpg.add_listbox((), tag=self.tag_listbox, callback=self.ui_select_table)
                    with dpg.group():
                        dpg.add_text('Limit')
                        dpg.add_input_text(tag='select_limit', default_value='10')
                with dpg.tab_bar(label='tabs'):
                    with dpg.tab(label='content'):
                        dpg.add_table(tag=self.tag_content, **self.table_params)
                    with dpg.tab(label='schema'):
                        dpg.add_table(tag=self.tag_schema, **self.table_params)

        dpg.create_viewport(title='Seeqler', width=800, height=500)
        dpg.set_primary_window(self.id_window, True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
