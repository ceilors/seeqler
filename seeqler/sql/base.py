from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine, Inspector, CursorResult


__all__ = ("BaseSQL", "BaseNoSQL")


_DRIVER_METHODS = ("connect", "raw", "select", "update", "insert", "delete", "alter")


class BaseSQLMeta(type):
    def __new__(cls: type["BaseSQLMeta"], name, bases, namespace) -> "BaseSQLMeta":

        namespace["methods"] = _DRIVER_METHODS

        implemented = set(namespace.keys())
        for base in bases:
            implemented.update(dir(base))

        # add not implemented but available methods from _DRIVER_METHODS defaults
        for method in _DRIVER_METHODS:
            if method in implemented:
                continue

            def make_func(klass, method):
                def func(*args, **kwargs):
                    raise NotImplementedError(f"{klass}.{method} is not implemented")

                return func

            namespace[method] = make_func(name, method)
        super_new = super().__new__(cls, name, bases, namespace)
        return super_new


class BaseSQL(metaclass=BaseSQLMeta):
    engine: Optional["Engine"] = None
    inspector: Optional["Inspector"] = None

    def raw(self, request, *args, **kwargs) -> "CursorResult":
        with self.engine.connect() as conn:
            return conn.execute(request, *args, **kwargs)

    @staticmethod
    def _stringify(value: str | int | list[str] | None, keyword: str = "", separator: str = ", ") -> str:
        if keyword and not keyword.endswith(" "):
            keyword += " "

        match value:
            case str() | int():
                return f" {keyword}{value}"
            case list() | tuple() | set():
                return " " + keyword + separator.join(map(str, value))
        return ""

    def select(
        self,
        distinct: bool = False,
        what: str | list[str] = "*",
        from_: str | list[str] | None = None,
        where: str | list[str] | None = None,
        group: str | list[str] | None = None,
        order: str | list[str] | None = None,
        limit: int | str | None = None,
    ):
        request = "select "
        if distinct:
            request += "distinct"

        request += self._stringify(what)
        request += self._stringify(from_, "from ")
        request += self._stringify(where, "where ", " and ")
        request += self._stringify(group, "group by ")
        request += self._stringify(order, "order by ")
        request += self._stringify(limit, "limit ")
        request += ";"

        return self.raw(request)


class BaseNoSQL:
    ...
