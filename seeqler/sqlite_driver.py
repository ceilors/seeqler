import sqlite3
import re

import dearpygui.dearpygui as dpg


pschema = re.compile(r'\((.*)\)')


def remap(item):
    if isinstance(item, int) or isinstance(item, float):
        return f'{item}'
    elif isinstance(item, str):
        return f"'{item}'"
    raise ValueError(f'type {type(item)} is unsupported!')


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# TODO: rewrite this shit
class SQLite:
    def __init__(self, filename):
        self._connection = sqlite3.connect(filename)
        self._connection.row_factory = dict_factory
        self._cursor = self._connection.cursor()

    def _execute_cmd(self, command):
        self._cursor.execute(command)
        self._connection.commit()
        return self._cursor.fetchall()

    def _execute_many(self, command):
        self._cursor.executescript(command)
        self._connection.commit()
        return self._cursor.fetchall()

    def _insert_one(self, table, data):
        keys = ', '.join(data.keys())
        values = ', '.join([remap(x) for x in data.values()])
        return f'insert into {table} ({keys}) values ({values});'

    def _insert_many(self, table, data):
        return '\n'.join([self._insert_one(table, item) for item in data])

    @property
    def tables(self):
        command = "select tbl_name from sqlite_master where type = 'table' order by tbl_name;"
        return [x.get('tbl_name') for x in self._execute_cmd(command)]

    def schema(self, table):
        command = f"select sql from sqlite_master where tbl_name = '{table}';"
        return self._execute_cmd(command)

    def create(self, name, schema):
        request = f'create table {name} ({schema});'
        return self._execute_cmd(request)

    def insert(self, table, data):
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._execute_many(self._insert_many(table, data))
            else:
                raise ValueError(f'type {type(data[0])} is unsupported!')
        elif isinstance(data, dict):
            return self._execute_many(self._insert_one(table, data))
        raise ValueError(f'type {type(data)} is unsupported!')

    def select(self, name):
        request = f'select * from {name};'
        return self._execute_cmd(request)


def parse_schema(schema):
    data = pschema.search(schema[0].get('sql'))
    return [x.strip().split() for x in data.group(1).split(',')]


if __name__ == '__main__':
    table_params = {
        'header_row': True,
        'borders_outerH': True, 'borders_innerV': True, 'borders_innerH': True, 'borders_outerV': True,
        'policy': dpg.mvTable_SizingFixedFit, 'resizable': True, 'no_host_extendX': True
    }
    db = SQLite('demo.sqlite3')
    schema = parse_schema(db.schema('table1'))

    dpg.create_context()
    dpg.create_viewport(title='Sequel Plus', width=800, height=500)

    with dpg.font_registry():
        default_font = dpg.add_font('FiraMono-Regular.ttf', 16)

    with dpg.window(label='Window', width=800):
        dpg.bind_font(default_font)

        with dpg.group(horizontal=True):
            with dpg.table(**table_params):
                dpg.add_table_column(label='Tables')
                for row in db.tables:
                    with dpg.table_row():
                        dpg.add_text(row)
            with dpg.table(**table_params):
                dpg.add_table_column(label='Param')
                dpg.add_table_column(label='Type')
                for p, t in schema:
                    with dpg.table_row():
                        dpg.add_text(p)
                        dpg.add_text(t)
            with dpg.table(**table_params):
                for p, _ in schema:
                    dpg.add_table_column(label=p)
                for data in db.select('table1'):
                    with dpg.table_row():
                        for key in data.keys():
                            dpg.add_text(data[key])

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

    # print(a.create('table1', 'id int, name text'))
    # print(a.insert('table1', [{'id': 1, 'name': 'hello'}, {'id': 2, 'name': 'world'}]))
    # print(a.create('table2', 'id int, a int, b int'))
    # print(a.insert('table2', {'id': 1, 'a': 1, 'b': 2}))
    # print('tables: ')
    # for row in a.tables:
    #     print(f' - {row}')
    # print('table1_schema:', a.schema('table1'))
    # print('table2_schema:', a.schema('table2'))
