from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from .common.types import SingletonMeta

if TYPE_CHECKING:
    from pathlib import Path

    from seeqler.common.language import Language

    from .common.connection_manager import Connection


@dataclass
class Settings(metaclass=SingletonMeta):
    lang: "Language"
    resources_path: "Path"
    rows_per_page: int = 100
    connection: Optional["Connection"] = None
    screen_width: int = 1024
    screen_height: int = 768
    font_list: List[int] = ("FiraMono-Regular.ttf", "FiraMono-Bold.ttf")
