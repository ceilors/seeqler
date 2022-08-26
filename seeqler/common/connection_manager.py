import json
import uuid as uuid_lib
from dataclasses import dataclass, asdict, field
from pathlib import Path

from .types import SingletonMeta


@dataclass
class Connection:
    label: str
    connection_string: str
    uuid: str = field(default_factory=lambda: str(uuid_lib.uuid4()))


DEFAULT_PATH = Path.home() / ".config" / "seeqler" / "connections.json"


class JsonAccessor:
    def __init__(self, path):
        self.path = path
        self.loading = None
        self.dumping = None

    def __enter__(self):
        try:
            self.loading = json.load(self.path.open())
        except json.JSONDecodeError:
            self.loading = []
        return self

    def __exit__(self, *exit_args):
        if self.dumping:
            json.dump(self.dumping, self.path.open("w"))


class ConnectionManager(metaclass=SingletonMeta):
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.open("w").write("[]")
        self.json_wrapper = JsonAccessor(self.path)

    def __iter__(self):
        yield from self.list()

    def list(self) -> list[Connection]:
        with self.json_wrapper as jsw:
            return [Connection(**i) for i in jsw.loading]

    def add(self, connection: Connection) -> None:
        with self.json_wrapper as jsw:
            data = jsw.loading
            data.append(asdict(connection))
            jsw.dumping = data

    def update(self, connection: Connection) -> None:
        with self.json_wrapper as jsw:
            data = jsw.loading
            for i, c in enumerate(data):
                if c["uuid"] == connection.uuid:
                    data[i] = asdict(connection)
                    break
            jsw.dumping = data

    def remove(self, connection: Connection) -> None:
        with self.json_wrapper as jsw:
            data = jsw.loading
            for i, c in enumerate(data):
                if c["uuid"] == connection.uuid:
                    del data[i]
                    break
            jsw.dumping = data

    def get(
        self, *, label: str | None = None, uuid: str | None = None, connection_string: str | None = None
    ) -> Connection:
        conns = self.list()
        match label, uuid, connection_string:
            case (None, str(req), None) | (str(req), None, None) | (None, None, str(req)):
                appropriate = list(
                    filter(
                        lambda conn: (conn.label if label else conn.uuid if uuid else conn.connection_string) == req,
                        conns,
                    )
                )
                if len(appropriate) != 1:
                    raise ValueError("No or multiple connections found")
                return appropriate[0]
            case _:
                raise ValueError("Incorrect arguments")
