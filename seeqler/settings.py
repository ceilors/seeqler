from typing import TYPE_CHECKING, Optional

from dataclasses import dataclass

from .common.types import SingletonMeta

if TYPE_CHECKING:
    from .common.connection_manager import Connection
    from seeqler.common.language import Language
    from pathlib import Path


@dataclass
class Settings(metaclass=SingletonMeta):
    lang: "Language"
    resources_path: "Path"
    rows_per_page: int = 100
    connection: Optional["Connection"] = None
    screen_width: int = 1024
    screen_height: int = 768
