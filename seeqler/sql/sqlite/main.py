from typing import TYPE_CHECKING

from ..base import BaseSQL

import sqlalchemy as sa

if TYPE_CHECKING:
    from seeqler.common.connection_manager import Connection


__all__ = ("SQLite",)


class SQLite(BaseSQL):
    def connect(self, connection: "Connection", *args, **kwargs) -> None:
        connection_string = connection.connection_string
        self.engine = sa.create_engine(connection_string)
        self.inspector = sa.inspect(self.engine)
