from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

if TYPE_CHECKING:
    from .app import Seeqler


def create_connection_list_window(seeqler: 'Seeqler', window_id='connection_list', *args, **kwargs):
    with dpg.window(label='Select connection', id=window_id):
        dpg.bind_font(seeqler.tag_default_font)

        with dpg.group(horizontal=False):
            with dpg.group(width=400):
                dpg.add_text('List of existing connections')
                dpg.add_listbox((), tag="self_tag_listbox")  # , callback=...)
            dpg.add_button(label='Create new connection...')


def create_connection_schema_window(seeqler: 'Seeqler', schemas: list[str], window_id='main_window', *args, **kwargs):
    with dpg.window(label='Window', id=window_id):
        dpg.bind_font(seeqler.tag_default_font)

        with dpg.group(horizontal=True):
            with dpg.group(width=200):
                dpg.add_text('Schemas')
                dpg.add_combo(schemas, tag=seeqler.tag_schema_selector, callback=seeqler.ui_select_schema)
                dpg.add_text('Tables')
                dpg.add_listbox((), tag=seeqler.tag_listbox, callback=seeqler.ui_select_table)
                with dpg.group():
                    dpg.add_text('Limit')
                    dpg.add_input_text(tag='select_limit', default_value='10')
            with dpg.tab_bar(label='tabs'):
                with dpg.tab(label='content'):
                    dpg.add_table(tag=seeqler.tag_content, **seeqler.table_params)
                with dpg.tab(label='schema'):
                    dpg.add_table(tag=seeqler.tag_schema, **seeqler.table_params)
