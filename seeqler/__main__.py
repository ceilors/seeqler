import sys
from pathlib import Path

import sqlalchemy as sa
import dearpygui.dearpygui as dpg


def main(connection_string: str):
    engine = sa.create_engine(connection_string)
    inspector = sa.inspect(engine)
    schemas = inspector.get_schema_names()
    tables = inspector.get_table_names(schema=schemas[0])
    current_table = tables[0]

    table_params = {
        'header_row': True,
        'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True, 'borders_outerV': True,
        'policy': dpg.mvTable_SizingFixedFit, 'resizable': True, 'no_host_extendX': True
    }

    def select_table(sender, value):
        tag = 'current table'
        dpg.delete_item(tag, children_only=True)
        table = dpg.get_value('table list')
        columns = inspector.get_columns(table)
        for c in columns:
            dpg.add_table_column(label=c['name'], parent=tag)
        with engine.connect() as conn:
            for row in conn.execute(f'select * from {table} limit 10'):
                with dpg.table_row(parent=tag):
                    for e in row:
                        dpg.add_text(e)


    def combo_callback(sender, value):
        dpg.configure_item('table list', items=inspector.get_table_names(schema=value))

    dpg.create_context()
    dpg.create_viewport(title='Seeqler', width=800, height=500)

    with dpg.item_handler_registry(tag="table list handler") as handler:
        dpg.add_item_clicked_handler(callback=select_table)


    with dpg.font_registry():
        default_font = dpg.add_font(Path(__file__).parent.parent / 'resources'/ 'FiraMono-Regular.ttf', 16)

    with dpg.window(label='Window', width=800):
        dpg.bind_font(default_font)

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_combo(schemas, tag='schema selector', callback=combo_callback)
                dpg.add_listbox((), tag='table list')
                dpg.add_table(tag='current table', **table_params)

    dpg.bind_item_handler_registry("table list", "table list handler")

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    main(sys.argv[1])
