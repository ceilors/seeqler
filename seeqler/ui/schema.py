import dearpygui.dearpygui as dpg

from .window import Window
from . import ConnectionListWindow


class SchemaWindow(Window):
    def __init__(self, inspector, engine, **kwargs):
        """Calls Window.__init__ with specified arguments. Passes inspector and engine as is."""

        # fmt: off
        super().__init__(
            inspector, engine, 'Текущее подключение', 'main_window', (800, 500), True, True,
            tag_schema_selector='schema selector', tag_listbox='table list', tag_content='current table',
            tag_schema='current schema', tag_handler='table list handler', tag_limit='select_limit',
            table_params = {
                'header_row': True, 'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True,
                'borders_outerV': True, 'resizable': True, 'no_host_extendX': True
            }, **kwargs
        )
        # fmt: on

    def construct(self) -> None:
        with dpg.group(horizontal=True):
            with dpg.group(width=200):
                dpg.add_text('Schemas')
                dpg.add_combo((), tag=self.tag_schema_selector, callback=self.ui_select_schema)
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

        # dummy button for tests
        dpg.add_button(label="Switch to connection list", callback=lambda x: ConnectionListWindow().show())

    def show(self) -> None:
        super().show()
        dpg.configure_item(self.tag_schema_selector, items=self.inspector.get_schema_names())

    def ui_select_table(self, sender, table=None):
        """Select table from schema and initiate tab panel"""

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
        """Select schema from schemas list."""

        dpg.configure_item(self.tag_listbox, items=sorted(self.inspector.get_table_names(schema=schema)))
        self.ui_select_table(sender)  # because listbox has selected item, but doesnt trigger callback itself
