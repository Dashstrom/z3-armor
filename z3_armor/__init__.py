"""Main module."""

from .algorithm import Z3Armor
from .cli import entrypoint
from .constraint import Constraint
from .info import (
    __author__,
    __email__,
    __license__,
    __maintainer__,
    __summary__,
    __version__,
)

__all__ = [
    "entrypoint",
    "__author__",
    "__email__",
    "__license__",
    "__maintainer__",
    "__summary__",
    "__version__",
    "Constraint",
    "Z3Armor",
]
