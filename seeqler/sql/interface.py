from typing import TYPE_CHECKING, Type

from .sqlite import SQLite

if TYPE_CHECKING:
    from ..common.connection_manager import Connection
    from .base import BaseSQL, BaseNoSQL


def driver_factory(dbms: str) -> Type["BaseSQL"] | Type["BaseNoSQL"]:
    """
    Get DBMS-specific driver.

    Arguments:
        dbms: name of database management system

    Returns:
        BaseSQL | BaseNoSQL: dbms driver

    Raises:
        NotImplementedError: if driver is not implemented
    """
    match dbms:
        case "sqlite":
            return SQLite
        case _:
            raise NotImplementedError(f"{dbms} driver is not implemented (yet?)")


class Interface:
    """
    Requesting interface for all the drivers.
    """

    _impl = None

    def __init__(self, dbms: str = "sqlite"):
        self._impl = (driver_factory(dbms))()
        self.provide_implementation()

    def provide_implementation(self) -> None:
        for method in self._impl.methods:
            if method == "connect":
                continue
            setattr(self, method, getattr(self._impl, method))

    def connect(self, conn: "Connection"):
        # basic entrypoint to work with connections
        # may need to have some common preparations here
        self._impl.connect(conn)
