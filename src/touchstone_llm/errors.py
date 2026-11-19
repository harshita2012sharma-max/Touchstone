"""Exception types shared across touchstone.

Every error touchstone raises on purpose subclasses :class:`TouchstoneError`, so the
CLI can show its message cleanly instead of a long traceback.
"""

from __future__ import annotations


class TouchstoneError(Exception):
    """Base class for expected, user-facing touchstone errors."""
