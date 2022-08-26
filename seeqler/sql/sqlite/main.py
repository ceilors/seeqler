from ..base import BaseSQL

import sqlalchemy as sa


__all__ = ("SQLite",)


class SQLite(BaseSQL):
    def connect(self, connection_string: str, *args, **kwargs) -> None:
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)

    def disconnect(self):
        if hasattr(self, "engine"):
            self.engine.dispose()
            del self.inspector
            del self.engine

    def __enter__(self):
        if not hasattr(self, "engine"):
            raise ValueError("Connect to DB first!")
        self.connection = self.engine.connect()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not hasattr(self, "connection"):
            return
        self.connection.close()
