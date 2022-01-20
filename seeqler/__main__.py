import sys
from pathlib import Path

import sqlalchemy as sa
import dearpygui.dearpygui as dpg


def main(connection_string: str):
    engine = sa.create_engine(connection_string)
    inspector = sa.inspect(engine)
    schemas = inspector.get_schema_names()
    tables = inspector.get_table_names(schema=schemas[0])
    columns = inspector.get_columns(tables[0])

    table_params = {
        'header_row': True,
        'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True, 'borders_outerV': True,
        'policy': dpg.mvTable_SizingFixedFit, 'resizable': True, 'no_host_extendX': True
    }

    dpg.create_context()
    dpg.create_viewport(title='Seeqler', width=800, height=500)

    with dpg.font_registry():
        default_font = dpg.add_font(Path(__file__).parent.parent / 'resources'/ 'FiraMono-Regular.ttf', 16)

    with dpg.window(label='Window', width=800):
        dpg.bind_font(default_font)

        with dpg.group(horizontal=True):
            with dpg.table(**table_params):
                dpg.add_table_column(label='Schemas')
                for row in schemas:
                    with dpg.table_row():
                        dpg.add_text(row)
            with dpg.table(**table_params):
                dpg.add_table_column(label='Tables')
                for row in tables:
                    with dpg.table_row():
                        dpg.add_text(row)
            with dpg.table(**table_params):
                for c in columns:
                    dpg.add_table_column(label=c['name'])
                with engine.connect() as conn:
                    for row in conn.execute(f'select * from {tables[0]} limit 10'):
                        with dpg.table_row():
                            for e in row:
                                dpg.add_text(e)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    main(sys.argv[1])
