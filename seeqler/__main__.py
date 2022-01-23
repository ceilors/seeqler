from pathlib import Path
import sys
import re

import sqlalchemy as sa
import dearpygui.dearpygui as dpg


tag_listbox = 'table list'
tag_content = 'current table'
tag_schema = 'current schema'
tag_handler = 'table list handler'
tag_limit = 'select_limit'
id_window = 'main_window'


def main(connection_string: str):
    engine = sa.create_engine(connection_string)
    inspector = sa.inspect(engine)
    schemas = inspector.get_schema_names()
    tables = inspector.get_table_names(schema=schemas[0])
    current_table = tables[0]

    table_params = {
        'header_row': True, 'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True,
        'borders_outerV': True, 'resizable': True, 'no_host_extendX': True
    }

    def select_table(sender, value):
        dpg.delete_item(tag_content, children_only=True)
        dpg.delete_item(tag_schema, children_only=True)

        table = dpg.get_value(tag_listbox)
        limit = dpg.get_value(tag_limit)

        columns = inspector.get_columns(table)
        for c in columns:
            dpg.add_table_column(label=c['name'], parent=tag_content)
        for column in ['param', 'type']:
            dpg.add_table_column(label=column, parent=tag_schema)

        with engine.connect() as conn:
            for row in conn.execute(f'select * from {table} limit {limit}'):
                with dpg.table_row(parent=tag_content):
                    for e in row:
                        dpg.add_text(e)

            for item in columns:
                with dpg.table_row(parent=tag_schema):
                    dpg.add_text(item['name'])
                    dpg.add_text(item['type'])


    def combo_callback(sender, value):
        dpg.configure_item(tag_listbox, items=inspector.get_table_names(schema=value))

    dpg.create_context()
    dpg.create_viewport(title='Seeqler', width=800, height=500)

    with dpg.item_handler_registry(tag=tag_handler) as handler:
        dpg.add_item_clicked_handler(callback=select_table)

    with dpg.font_registry():
        default_font = dpg.add_font(Path(__file__).parent.parent / 'resources'/ 'FiraMono-Regular.ttf', 16)

    with dpg.window(label='Window', id=id_window):
        dpg.bind_font(default_font)

        with dpg.group(horizontal=True):
            with dpg.group(width=200):
                dpg.add_text('Schemas')
                dpg.add_combo(schemas, tag='schema selector', callback=combo_callback)
                dpg.add_text('Tables')
                dpg.add_listbox((), tag=tag_listbox)
                with dpg.group():
                    dpg.add_text('Limit')
                    dpg.add_input_text(tag='select_limit', default_value='10')
            with dpg.tab_bar(label='tabs'):
                with dpg.tab(label='content'):
                    dpg.add_table(tag=tag_content, **table_params)
                with dpg.tab(label='schema'):
                    dpg.add_table(tag=tag_schema, **table_params)

    dpg.bind_item_handler_registry(tag_listbox, tag_handler)

    dpg.set_primary_window(id_window, True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == '__main__':
    main(sys.argv[1])
