from typing import TYPE_CHECKING, Type

from .sqlite import SQLite

if TYPE_CHECKING:
    from ..common.connection_manager import Connection
    from .base import BaseNoSQL, BaseSQL


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


def ensure_connected(func):
    def wrapper(self, *args, **kwargs):
        if not self.connected:
            raise ValueError("Interface is not connected")

        return func(self, *args, **kwargs)

    return wrapper


NOT_COPIED_METHODS = ("connect", "disconnect")


class Interface:
    """
    Requesting interface for all the drivers.
    """

    _impl = None

    def __init__(self, dbms: str = "sqlite"):
        self._type = dbms
        self._impl = (driver_factory(self._type))()
        self.provide_implementation()
        self.connected = False

    def provide_implementation(self) -> None:
        for method in self._impl.methods:
            if method in NOT_COPIED_METHODS:
                continue

            def make_func(method_name):
                @ensure_connected
                def func(self, *args, **kwargs):
                    return getattr(self._impl, method_name)(*args, **kwargs)

                return func

            setattr(self, method, make_func(method).__get__(self, Interface))

    def connect(self, conn: "Connection"):
        # basic entrypoint to work with connections
        # may need to have some common preparations here
        self._impl.connect(conn.connection_string)
        self.engine = self._impl.engine
        self.inspector = self._impl.inspector
        self.connected = True

    @ensure_connected
    def disconnect(self):
        self._impl.disconnect()
