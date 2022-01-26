import json
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict, field

from .common import SingletonMeta


@dataclass
class Connection:
    label: str
    connection_string: str
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


DEFAULT_PATH = Path.home() / '.config' / 'seeqler' / 'connections.json'


class ConnectionManager(metaclass=SingletonMeta):
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.open('w').write('[]')

    def list(self) -> list[Connection]:
        data = json.load(self.path.open())
        return [Connection(**i) for i in data]

    def add(self, connection: Connection) -> None:
        with self.path.open('rw') as f:
            data = json.load(f)
            data.append(asdict(connection))
            json.dump(data, f)

    def update(self, connection: Connection) -> None:
        with self.path.open('rw') as f:
            data = json.load(f)
            for i, c in enumerate(data):
                if c['uuid'] == connection.uuid:
                    data[i] = asdict(connection)
                    break
            json.dump(data, f)

    def remove(self, connection: Connection) -> None:
        with self.path.open('rw') as f:
            data = json.load(f)
            for i, c in enumerate(data):
                if c['uuid'] == connection.uuid:
                    del data[i]
                    break
            json.dump(data, f)
