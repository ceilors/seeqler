import sqlite3


def get_tables(connection):
    cursor = connection.cursor()
    request = cursor.execute('select name from sqlite_master;')
    return request.fetchall()


def create_demo_table(connection, name):
    create_request = 'create table demo (id int, name text);'
    cursor = connection.cursor()
    cursor.execute(create_request)
    return connection.commit()


if __name__ == '__main__':
    connection = sqlite3.connect('demo.sqlite3')
    tables = get_tables(connection)
    if len(tables) == 0:
        create_demo_table(connection, 'demo')
        tables = get_tables(connection)
    print(tables)
