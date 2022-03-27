from typing import TYPE_CHECKING, Union

from .sqlite import SQLite

if TYPE_CHECKING:
    from .base import BaseSQL, BaseNoSQL


def driver_factory(dbms: str = "sqlite") -> Union["BaseSQL", "BaseNoSQL"]:
    """Get DBMS-specific driver.

    Args:
        dmbs: name of database management system

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
    _impl = None

    def __init__(self):
        self._impl = (driver_factory())()
        self.provide_implementation()

    def provide_implementation(self) -> None:
        # TODO: change to descriptor?
        for method in self._impl.methods:
            setattr(self, method, getattr(self._impl, method))
