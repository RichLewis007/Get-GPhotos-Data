"""Update checking system (stub implementation).

This module provides a framework for checking application updates.
Currently implemented as a stub that always reports no updates available.

For a full implementation, this would:
- Make HTTP requests to check for new versions
- Parse version information from JSON responses
- Compare semantic versions
- Emit signals when updates are available

The stub demonstrates the API contract that a real implementation would follow.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal


class UpdateChecker(QObject):
    """Stub for update checking functionality (non-auto install)."""

    update_available = Signal(str, str)  # version, release_notes_url
    no_update = Signal()
    check_failed = Signal(str)  # error message

    def __init__(self, current_version: str, check_url: str = "") -> None:
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.current_version = current_version
        self.check_url = (
            check_url or "https://api.github.com/repos/example/get-gphotos-data/releases/latest"
        )

    def check_for_updates(
        self,
        on_available: Callable[[str, str], None] | None = None,
        on_no_update: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """
        Check for updates (stub implementation).

        In a real implementation, this would:
        1. Make an HTTP request to check_url
        2. Parse version information
        3. Compare with current_version
        4. Emit appropriate signals

        This stub always reports no update available.
        """
        self.log.info("Update check requested (stub - no actual check performed)")

        # Connect callbacks if provided
        if on_available:
            self.update_available.connect(lambda v, u: on_available(v, u))
        if on_no_update:
            self.no_update.connect(on_no_update)
        if on_error:
            self.check_failed.connect(on_error)

        # Stub: always report no update
        # In a real implementation, you would:
        # - Use QNetworkAccessManager for HTTP requests
        # - Parse JSON response
        # - Compare semantic versions
        # - Emit update_available or no_update accordingly

        self.no_update.emit()
