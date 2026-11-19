"""Exception types shared across kasauti.

Every error kasauti raises on purpose subclasses :class:`KasautiError`, so the
CLI can show its message cleanly instead of a long traceback.
"""

from __future__ import annotations


class KasautiError(Exception):
    """Base class for expected, user-facing kasauti errors."""
