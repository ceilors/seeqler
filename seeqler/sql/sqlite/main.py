from ..base import BaseSQL

import sqlalchemy as sa


__all__ = ("SQLite",)


class SQLite(BaseSQL):
    def connect(self, connection_string, *args, **kwargs) -> None:
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)
