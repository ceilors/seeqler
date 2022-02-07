import toga
from toga.style import Pack
from toga.constants import ROW, COLUMN

from .window import Window
from . import ConnectionListWindow


class SchemaWindow(Window):
    def __init__(self, app, **kwargs):
        self.lang = app.seeqler.lang
        self.connection_params = {}
        self.current_content = ""

        super().__init__(app, self.lang.sw_win_schema, "main_window", (800, 500), on_close=self.ui_disconnect, **kwargs)

    def get_content(self) -> toga.Widget:
        root = toga.Box(style=Pack(direction=ROW))

        left_side = toga.Box(style=Pack(padding=10, direction=COLUMN, width=200))

        style = self.style
        style.update(padding_bottom=10)

        left_side.add(toga.Label(self.lang.sw_lbl_schemas, style=style))
        self.schema_selector = toga.Table(
            [self.lang.sw_txt_schema_name], style=self.style, on_select=self.ui_select_schema, missing_value="—"
        )
        self.schema_selector.style.update(padding_bottom=15)
        left_side.add(self.schema_selector)

        left_side.add(toga.Label(self.lang.sw_lbl_tables, style=style))
        self.table_selector = toga.Table([self.lang.sw_txt_table_name], style=self.style, missing_value="—")
        self.table_selector.style.update(padding_bottom=15)
        left_side.add(self.table_selector)

        left_side.add(toga.Label(self.lang.sw_lbl_limit, style=style))
        self.limit_input = toga.NumberInput(style=style, default=10)
        self.limit_input.style.update(padding_bottom=30)
        left_side.add(self.limit_input)

        left_side.add(toga.Button(self.lang.sw_btn_disconnect, style=self.style, on_press=self.ui_disconnect))

        right_side = toga.Box(style=Pack(padding=10, direction=COLUMN))

        toolbar = toga.Box(style=Pack(direction=ROW, padding_bottom=10))

        widget = toga.Button(self.lang.sw_btn_content_tab, id="btn_content", on_press=self.switch_tab, style=self.style)
        widget.style.update(padding_right=10)
        toolbar.add(widget)
        widget = toga.Button(self.lang.sw_btn_schema_tab, id="btn_schema", on_press=self.switch_tab, style=self.style)
        toolbar.add(widget)

        right_side.add(toolbar)

        self.tab_content = toga.Box(style=Pack(flex=1))
        right_side.add(self.tab_content)

        split = toga.SplitContainer()
        split.content = [left_side, right_side]

        root.add(split)

        return root

    def switch_tab(self, button: toga.Button | None = None) -> None:
        tab = "content"
        if button:
            tab = str(button.id).split("_", maxsplit=1)[-1]

        if not self.connection_params or self.current_content == tab:
            return

        schema, table, limit = self.connection_params
        columns = self.app.seeqler.inspector.get_columns(table, schema=schema)
        if tab == "content":
            headers = [c["name"] for c in columns]
            data = []

            with self.app.seeqler.engine.connect() as conn:
                for row in conn.execute(f"select * from {table} limit {limit}"):
                    data.append(row)
        else:
            headers = ["param", "type", "nullable", "default", "foreign key"]
            data = []

            foreign_keys = {
                i["constrained_columns"][0]: "{referred_schema}.{referred_table}({referred_columns[0]})".format(**i)
                for i in self.app.seeqler.inspector.get_foreign_keys(table, schema=schema)
            }
            for item in columns:
                data.append(
                    [item["name"], item["type"], item["nullable"], item["default"], foreign_keys.get(item["name"])]
                )

        self.current_content = tab
        self.tab_content.add(toga.Table(headings=headers, style=self.style, data=data, missing_value="—"))

    def show(self) -> None:
        super().show()
        names = self.app.seeqler.inspector.get_schema_names()
        for name in names:
            self.schema_selector.data.append(name)

    def ui_disconnect(self, widget=None) -> None:
        conn_list = ConnectionListWindow(self.app)
        self.app.main_window = conn_list.get_window()
        conn_list.show()
        self.app.seeqler.engine = None
        self.app.seeqler.inspector = None
        self.hide()

    def _get_schema_name(self, row=None) -> str | None:
        if not row:
            row = self.schema_selector.selection
        return getattr(row, self.lang.sw_txt_schema_name.lower(), None)

    def _get_table_name(self, row=None) -> str | None:
        if not row:
            row = self.table_selector.selection
        return getattr(row, self.lang.sw_txt_table_name.lower(), None)

    def ui_select_schema(self, table, row):
        """Select schema from schemas list."""

        name = self._get_schema_name(row)
        if not name:
            return

        items = sorted(self.app.seeqler.inspector.get_table_names(schema=name))
        for item in items:
            self.table_selector.data.append(item)

    def ui_select_table(self, table, row):
        """Select table from schema and initiate tab panel"""
        self.tab_content.remove(*self.tab_content.children)

        schema = self._get_schema_name()
        if not schema:
            return

        table_name = self._get_table_name(row)
        if not table_name:
            return

        limit = self.limit_input.value

        self.connection_params = {"schema": schema, "table": table_name, "limit": limit}
        self.current_content = ""  # clean current_content to update widget
        self.switch_tab()
