"""Research-only Tushare minimal staging proof."""

from .client import TushareMinimalClient
from .pit_contract import build_pit_records
from .schemas import INTERFACE_SCHEMAS
from .validators import validate_interface_frame

__all__ = [
    "INTERFACE_SCHEMAS",
    "TushareMinimalClient",
    "build_pit_records",
    "validate_interface_frame",
]
