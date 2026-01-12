"""Google Photos data viewer widget.

This widget displays Google Photos data retrieved from the API,
including media items, albums, and shared albums.
"""

from __future__ import annotations

import contextlib
import json
import logging
import webbrowser
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.paths import app_data_dir, app_executable_dir
from ..core.ui_loader import load_ui
from ..core.workers import WorkContext, Worker, WorkerPool, WorkRequest
from ..photos.auth import GooglePhotosAuth
from ..photos.picker import GooglePhotosPicker

# Type alias for worker result tuple
WorkerResult = tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]

# Token file name (same as in auth.py)
TOKEN_FILE = "google_photos_token.json"


class GooglePhotosView(QWidget):
    """Widget for viewing Google Photos data from the API."""

    # Signal emitted when authentication status changes
    authenticated_changed = Signal(bool)

    def __init__(self, parent=None, debug_api: bool = False) -> None:
        """Initialize the Google Photos viewer widget.

        Args:
            parent: Parent widget
            debug_api: If True, enable detailed API logging to console
        """
        super().__init__(parent)
        self.log = logging.getLogger(__name__)
        self.debug_api = debug_api

        # Load UI from .ui file
        ui_widget = load_ui("google_photos_view.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find widgets
        auth_status_label = ui_widget.findChild(QLabel, "authStatusLabel")
        if auth_status_label is None:
            raise RuntimeError("authStatusLabel not found in google_photos_view.ui")
        self.auth_status_label = cast(QLabel, auth_status_label)

        authenticate_button = ui_widget.findChild(QPushButton, "authenticateButton")
        if authenticate_button is None:
            raise RuntimeError("authenticateButton not found in google_photos_view.ui")
        self.authenticate_button = cast(QPushButton, authenticate_button)

        refresh_button = ui_widget.findChild(QPushButton, "refreshButton")
        if refresh_button is None:
            raise RuntimeError("refreshButton not found in google_photos_view.ui")
        self.refresh_button = cast(QPushButton, refresh_button)

        data_tabs = ui_widget.findChild(QTabWidget, "dataTabs")
        if data_tabs is None:
            raise RuntimeError("dataTabs not found in google_photos_view.ui")
        self.data_tabs = cast(QTabWidget, data_tabs)

        # Media Items tab
        media_items_count_label = ui_widget.findChild(QLabel, "mediaItemsCountLabel")
        if media_items_count_label is None:
            raise RuntimeError("mediaItemsCountLabel not found in google_photos_view.ui")
        self.media_items_count_label = cast(QLabel, media_items_count_label)

        media_items_table = ui_widget.findChild(QTableWidget, "mediaItemsTable")
        if media_items_table is None:
            raise RuntimeError("mediaItemsTable not found in google_photos_view.ui")
        self.media_items_table = cast(QTableWidget, media_items_table)

        # Albums tab
        albums_count_label = ui_widget.findChild(QLabel, "albumsCountLabel")
        if albums_count_label is None:
            raise RuntimeError("albumsCountLabel not found in google_photos_view.ui")
        self.albums_count_label = cast(QLabel, albums_count_label)

        albums_table = ui_widget.findChild(QTableWidget, "albumsTable")
        if albums_table is None:
            raise RuntimeError("albumsTable not found in google_photos_view.ui")
        self.albums_table = cast(QTableWidget, albums_table)

        # Shared Albums tab
        shared_albums_count_label = ui_widget.findChild(QLabel, "sharedAlbumsCountLabel")
        if shared_albums_count_label is None:
            raise RuntimeError("sharedAlbumsCountLabel not found in google_photos_view.ui")
        self.shared_albums_count_label = cast(QLabel, shared_albums_count_label)

        shared_albums_table = ui_widget.findChild(QTableWidget, "sharedAlbumsTable")
        if shared_albums_table is None:
            raise RuntimeError("sharedAlbumsTable not found in google_photos_view.ui")
        self.shared_albums_table = cast(QTableWidget, shared_albums_table)

        # Details tab
        details_text = ui_widget.findChild(QTextEdit, "detailsText")
        if details_text is None:
            raise RuntimeError("detailsText not found in google_photos_view.ui")
        self.details_text = cast(QTextEdit, details_text)
        
        # Create image display label for photos and add it to details tab
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("No image selected")
        self.image_label.setMinimumHeight(200)
        self.image_label.setMaximumHeight(400)
        self.image_label.setStyleSheet(
            "border: 1px solid gray; background-color: #f0f0f0;"
        )
        # Don't use setScaledContents - we'll handle scaling manually to preserve aspect ratio
        self.image_label.setScaledContents(False)
        
        # Add image label to details tab (insert before detailsText)
        details_tab = ui_widget.findChild(QWidget, "detailsTab")
        if details_tab:
            details_layout = details_tab.layout()
            if details_layout:
                # Insert image label before the detailsText widget
                self.image_label.setVisible(True)
                details_layout.insertWidget(1, self.image_label)
                self.log.info("Image label added to details tab")

        # Connect signals
        self.authenticate_button.clicked.connect(self.on_authenticate)
        self.refresh_button.clicked.connect(self.on_refresh_data)

        # Connect table selection changes to show details
        self.media_items_table.itemSelectionChanged.connect(self.on_media_item_selected)
        self.albums_table.itemSelectionChanged.connect(self.on_album_selected)
        self.shared_albums_table.itemSelectionChanged.connect(self.on_shared_album_selected)

        # Initialize state
        self.auth: GooglePhotosAuth | None = None
        self.picker: GooglePhotosPicker | None = None
        self.media_items: list[dict[str, Any]] = []
        self.albums: list[dict[str, Any]] = []
        self.shared_albums: list[dict[str, Any]] = []
        self.pool = WorkerPool()
        self.active_worker: Worker[WorkerResult] | None = None
        self.poll_timer: QTimer | None = None
        self.current_session_id: str | None = None

        # Disable authenticate button by default
        self.authenticate_button.setEnabled(False)

        self._update_ui_state(False)

        # Try to load credentials.json from program's directory
        # This will enable the authenticate button if credentials.json is not found
        self._try_load_credentials()

    def set_credentials_path(self, credentials_path: Path | str) -> None:
        """Set the path to the OAuth credentials file.

        Args:
            credentials_path: Path to credentials.json file
        """
        self.auth = GooglePhotosAuth(credentials_path)
        # Check if already authenticated
        if self.auth.is_authenticated():
            try:
                credentials = self.auth.authenticate()
                self.picker = GooglePhotosPicker(
                    credentials, debug=self.debug_api
                )
                self._update_ui_state(True)
            except Exception as e:
                self.log.warning("Failed to initialize picker client: %s", e)
                self._update_ui_state(False)

    def _update_ui_state(self, authenticated: bool) -> None:
        """Update UI based on authentication state.

        Args:
            authenticated: Whether user is authenticated
        """
        if authenticated:
            self.auth_status_label.setText("Authenticated")
            self.authenticate_button.setText("Re-authenticate")
            self.authenticate_button.setEnabled(True)
            self.refresh_button.setEnabled(True)
        else:
            self.auth_status_label.setText("Not authenticated")
            self.authenticate_button.setText("Authenticate")
            # Don't disable authenticate button here - let _try_load_credentials handle it
            self.refresh_button.setEnabled(False)
            # Clear data
            self._clear_all_tables()

        self.authenticated_changed.emit(authenticated)

    def _try_load_credentials(self) -> None:
        """Try to load credentials.json from the program's directory.

        If credentials.json is found and a token file exists,
        attempts to authenticate automatically.
        If not found or authentication fails, enables the authenticate button.
        """
        app_dir = app_executable_dir()
        credentials_path = app_dir / "credentials.json"
        token_path = app_data_dir() / TOKEN_FILE

        if credentials_path.exists():
            self.log.info("Found credentials.json in program directory: %s", credentials_path)
            # Only auto-authenticate if a token file exists (user has authenticated before)
            if token_path.exists():
                try:
                    # Create auth instance and attempt to authenticate
                    self.auth = GooglePhotosAuth(credentials_path)
                    # Try to authenticate (will load existing token and refresh if needed)
                    credentials = self.auth.authenticate()
                    # If we got here, authentication succeeded
                    self.picker = GooglePhotosPicker(
                        credentials, debug=self.debug_api
                    )
                    self._update_ui_state(True)
                    self.log.info("Successfully authenticated with existing credentials")
                except Exception as e:
                    # Authentication failed - user may need to re-authenticate
                    self.log.warning("Failed to authenticate automatically: %s", e)
                    # Keep auth instance for manual auth
                    self.auth = GooglePhotosAuth(credentials_path)
                    self.picker = None
                    self._update_ui_state(False)
                    self.authenticate_button.setEnabled(True)
            else:
                # Credentials file exists but no token - user needs to authenticate
                self.log.info(
                    "credentials.json found but no token file - user needs to authenticate"
                )
                self.auth = GooglePhotosAuth(credentials_path)
                self.authenticate_button.setEnabled(True)
        else:
            self.log.info("credentials.json not found in program directory: %s", app_dir)
            # Enable authenticate button if credentials file not found
            self.authenticate_button.setEnabled(True)

    def on_authenticate(self) -> None:
        """Handle authenticate button click."""
        if self.auth is None:
            # Prompt for credentials file
            credentials_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Google Photos Credentials File",
                str(Path.home()),
                "JSON Files (*.json);;All Files (*)",
            )
            if not credentials_path:
                return
            self.auth = GooglePhotosAuth(credentials_path)

        try:
            credentials = self.auth.authenticate()
            self.picker = GooglePhotosPicker(
                credentials, debug=self.debug_api
            )
            self._update_ui_state(True)
            QMessageBox.information(
                self, "Authentication", "Successfully authenticated with Google Photos!"
            )
            # Note: Picker API requires user to select photos, so we don't auto-refresh
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Authentication Error", f"Credentials file not found:\n{e}")
        except Exception as e:
            self.log.exception("Authentication failed")
            QMessageBox.critical(self, "Authentication Error", f"Failed to authenticate:\n{e}")

    def on_refresh_data(self) -> None:
        """Open Google Photos Picker to select photos.

        Uses the Google Photos Picker API which allows access to all photos
        in the user's library (not just app-created content).
        """
        if not self.picker:
            QMessageBox.warning(self, "Not Authenticated", "Please authenticate first.")
            return

        if self.active_worker is not None or self.current_session_id:
            QMessageBox.information(
                self, "Loading", "A picker session is already active. Please wait."
            )
            return

        # Store picker in local variable for type narrowing
        picker = self.picker
        assert picker is not None  # Type narrowing

        # Create progress dialog
        progress_dialog = QProgressDialog(
            "Opening Google Photos Picker...", "Cancel", 0, 100, self
        )
        progress_dialog.setWindowTitle("Google Photos Picker")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setValue(0)

        # Show progress
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Opening Picker...")

        def work(ctx: WorkContext) -> dict[str, Any]:
            """Background work function - creates picker session.

            Returns session data with pickerUri.
            """
            ctx.progress(50, "Creating picker session...")
            ctx.check_cancelled()
            session = picker.create_session()
            ctx.progress(100, "Session created")
            return session

        def progress(percent: int, message: str) -> None:
            """Progress callback - runs on main thread via signal."""
            progress_dialog.setValue(percent)
            if message:
                progress_dialog.setLabelText(message)
                self.refresh_button.setText(message)
            # Process events to update UI
            progress_dialog.show()

        def done(session_data: dict[str, Any]) -> None:
            """Completion callback - opens picker and starts polling."""
            progress_dialog.close()

            # API returns "id" not "sessionId"
            session_id = session_data.get("id")
            picker_uri = session_data.get("pickerUri")

            if not session_id or not picker_uri:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to create picker session. Missing id or pickerUri.",
                )
                self.refresh_button.setEnabled(True)
                self.refresh_button.setText("Refresh Data")
                self.active_worker = None
                return

            self.current_session_id = session_id

            # Open picker in browser
            self.log.info("Opening picker URI in browser: %s", picker_uri)
            webbrowser.open(picker_uri)

            # Update UI
            self.refresh_button.setText("Waiting for selection...")
            progress_dialog.setLabelText(
                "Please select photos in the browser window.\n"
                "The app will automatically detect when you're done."
            )
            progress_dialog.setValue(50)
            progress_dialog.show()

            # Start polling for session completion
            self._start_polling_session(session_id, progress_dialog)

        def cancelled() -> None:
            """Cancellation callback - runs on main thread when work is cancelled."""
            progress_dialog.close()
            if self.current_session_id and self.picker:
                with contextlib.suppress(Exception):
                    self.picker.delete_session(self.current_session_id)
                self.current_session_id = None
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("Refresh Data")
            self.active_worker = None
            self.log.info("Picker session cancelled")

        def error(msg: str) -> None:
            """Error callback - runs on main thread when work fails."""
            progress_dialog.close()
            error_msg = msg
            # Provide helpful guidance for 403 errors
            if "403" in error_msg or "Forbidden" in error_msg:
                error_msg = (
                    f"403 Forbidden Error:\n{error_msg}\n\n"
                    "This usually means:\n"
                    "1. The Google Photos Picker API is not enabled in your Google Cloud Console\n"
                    "   → Go to APIs & Services > Library > Enable 'Google Photos Picker API'\n"
                    "2. The OAuth scope was not granted during authentication\n"
                    "   → Try re-authenticating and make sure to grant all permissions\n"
                    "3. The scope is not added to your OAuth consent screen\n"
                    "   → Add 'https://www.googleapis.com/auth/"
                    "photospicker.mediaitems.readonly' to scopes"
                )
            QMessageBox.critical(self, "Error", error_msg)
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("Refresh Data")
            self.active_worker = None
            self.log.exception("Failed to create picker session")

        # Connect cancel button to worker cancellation
        def cancel_work() -> None:
            if self.active_worker is not None:
                self.active_worker.cancel()

        progress_dialog.canceled.connect(cancel_work)

        req = WorkRequest(
            fn=work,
            on_done=done,
            on_error=error,
            on_progress=progress,
            on_cancel=cancelled,
        )
        self.active_worker = self.pool.submit(req)

    def _start_polling_session(
        self, session_id: str, progress_dialog: QProgressDialog
    ) -> None:
        """Start polling for session completion.

        Args:
            session_id: The session ID to poll
            progress_dialog: Progress dialog to update
        """
        if not self.picker:
            return

        # Stop any existing timer
        if self.poll_timer:
            self.poll_timer.stop()

        # Create timer to poll session status
        self.poll_timer = QTimer(self)
        poll_count = [0]  # Use list to allow modification in nested function

        def poll() -> None:
            """Poll session status and handle completion."""
            if not self.picker or not self.current_session_id:
                if self.poll_timer:
                    self.poll_timer.stop()
                return

            try:
                session = self.picker.get_session(session_id)
                # Check mediaItemsSet field - when True, user has completed selection
                media_items_set = session.get("mediaItemsSet", False)
                status = session.get("status", "")

                poll_count[0] += 1
                progress_dialog.setValue(50 + min(poll_count[0] * 2, 45))
                
                # Log status for debugging
                if poll_count[0] % 10 == 0:  # Log every 10 polls (every 20 seconds)
                    self.log.info(
                        "Polling session %s: mediaItemsSet=%s, status=%s",
                        session_id[:8],
                        media_items_set,
                        status,
                    )

                # Session is complete when mediaItemsSet is True
                if media_items_set or status == "SESSION_STATUS_COMPLETE":
                    # Session completed, get selected items
                    self.poll_timer.stop()
                    progress_dialog.setValue(90)
                    progress_dialog.setLabelText("Retrieving selected photos...")

                    # Capture picker and session_id for nested function
                    picker_instance = self.picker
                    captured_session_id = session_id

                    def fetch_items(ctx: WorkContext) -> list[dict[str, Any]]:
                        """Fetch selected items in background worker."""
                        ctx.progress(90, "Retrieving selected photos...")
                        if not picker_instance:
                            raise RuntimeError("Picker instance not available")
                        media_items = picker_instance.get_all_selected_media_items(
                            captured_session_id
                        )
                        # Clean up session
                        picker_instance.delete_session(captured_session_id)
                        ctx.progress(100, "Complete")
                        return media_items

                    def items_done(media_items: list[dict[str, Any]]) -> None:
                        """Handle fetched items on main thread."""
                        progress_dialog.close()

                        # Update data
                        self.media_items = media_items
                        self.albums = []  # Picker API doesn't return albums
                        self.shared_albums = []

                        # Populate tables
                        self._populate_media_items_table()
                        self._populate_albums_table()
                        self._populate_shared_albums_table()

                        # Show completion message
                        QMessageBox.information(
                            self,
                            "Photos Selected",
                            f"Loaded {len(self.media_items)} selected media items.",
                        )

                        # Reset UI
                        self.refresh_button.setEnabled(True)
                        self.refresh_button.setText("Refresh Data")
                        self.current_session_id = None
                        self.active_worker = None
                        self.log.info(
                            "Picker session completed with %d items",
                            len(self.media_items),
                        )

                    def items_error(msg: str) -> None:
                        """Handle fetch error on main thread."""
                        progress_dialog.close()
                        QMessageBox.critical(
                            self, "Error", f"Failed to retrieve selected photos:\n{msg}"
                        )
                        self.refresh_button.setEnabled(True)
                        self.refresh_button.setText("Refresh Data")
                        self.current_session_id = None
                        self.active_worker = None

                    # Fetch items in background worker
                    req = WorkRequest(
                        fn=fetch_items, on_done=items_done, on_error=items_error
                    )
                    self.active_worker = self.pool.submit(req)

                elif status == "SESSION_STATUS_EXPIRED":
                    self.poll_timer.stop()
                    progress_dialog.close()
                    QMessageBox.warning(
                        self, "Session Expired", "The picker session expired. Please try again."
                    )
                    self.refresh_button.setEnabled(True)
                    self.refresh_button.setText("Refresh Data")
                    self.current_session_id = None
                    self.active_worker = None

                # Continue polling if still active
                elif status == "SESSION_STATUS_ACTIVE" or not media_items_set:
                    if poll_count[0] > 300:  # 5 minutes timeout (2 second intervals)
                        self.poll_timer.stop()
                        progress_dialog.close()
                        QMessageBox.warning(
                            self,
                            "Timeout",
                            "Picker session timed out. Please try again.",
                        )
                        if self.picker:
                            with contextlib.suppress(Exception):
                                self.picker.delete_session(session_id)
                        self.refresh_button.setEnabled(True)
                        self.refresh_button.setText("Refresh Data")
                        self.current_session_id = None
                        self.active_worker = None

            except Exception as e:
                self.log.exception("Error polling session status")
                self.poll_timer.stop()
                progress_dialog.close()
                QMessageBox.critical(
                    self, "Error", f"Failed to check picker status:\n{e}"
                )
                self.refresh_button.setEnabled(True)
                self.refresh_button.setText("Refresh Data")
                self.current_session_id = None
                self.active_worker = None

        # Poll every 2 seconds
        self.poll_timer.timeout.connect(poll)
        self.poll_timer.start(2000)  # 2 seconds

    def _clear_all_tables(self) -> None:
        """Clear all data tables."""
        self.media_items_table.setRowCount(0)
        self.albums_table.setRowCount(0)
        self.shared_albums_table.setRowCount(0)
        self.media_items_count_label.setText("0 media items")
        self.albums_count_label.setText("0 albums")
        self.shared_albums_count_label.setText("0 shared albums")
        self.details_text.clear()

    def _populate_media_items_table(self) -> None:
        """Populate the media items table."""
        self.media_items_table.setRowCount(len(self.media_items))
        self.media_items_count_label.setText(f"{len(self.media_items)} media items")

        for row, item in enumerate(self.media_items):
            # ID
            id_item = QTableWidgetItem(item.get("id", ""))
            id_item.setData(Qt.ItemDataRole.UserRole, item)  # Store full item data
            self.media_items_table.setItem(row, 0, id_item)

            # Filename
            filename_item = QTableWidgetItem(item.get("filename", ""))
            self.media_items_table.setItem(row, 1, filename_item)

            # MIME Type
            mime_item = QTableWidgetItem(item.get("mimeType", ""))
            self.media_items_table.setItem(row, 2, mime_item)

            # Created time
            metadata = item.get("mediaMetadata", {})
            created_item = QTableWidgetItem(metadata.get("creationTime", ""))
            self.media_items_table.setItem(row, 3, created_item)

            # Dimensions
            width = metadata.get("width", "")
            height = metadata.get("height", "")
            dims_item = QTableWidgetItem(f"{width} × {height}" if width and height else "")
            self.media_items_table.setItem(row, 4, dims_item)

        # Resize columns to content
        self.media_items_table.resizeColumnsToContents()

    def _populate_albums_table(self) -> None:
        """Populate the albums table."""
        self.albums_table.setRowCount(len(self.albums))
        self.albums_count_label.setText(f"{len(self.albums)} albums")

        for row, album in enumerate(self.albums):
            # ID
            id_item = QTableWidgetItem(album.get("id", ""))
            id_item.setData(Qt.ItemDataRole.UserRole, album)  # Store full album data
            self.albums_table.setItem(row, 0, id_item)

            # Title
            title_item = QTableWidgetItem(album.get("title", ""))
            self.albums_table.setItem(row, 1, title_item)

            # Items count
            count_item = QTableWidgetItem(str(album.get("mediaItemsCount", 0)))
            self.albums_table.setItem(row, 2, count_item)

            # Writeable
            writeable_item = QTableWidgetItem("Yes" if album.get("isWriteable", False) else "No")
            self.albums_table.setItem(row, 3, writeable_item)

        # Resize columns to content
        self.albums_table.resizeColumnsToContents()

    def _populate_shared_albums_table(self) -> None:
        """Populate the shared albums table."""
        self.shared_albums_table.setRowCount(len(self.shared_albums))
        self.shared_albums_count_label.setText(f"{len(self.shared_albums)} shared albums")

        for row, album in enumerate(self.shared_albums):
            # ID
            id_item = QTableWidgetItem(album.get("id", ""))
            id_item.setData(Qt.ItemDataRole.UserRole, album)  # Store full album data
            self.shared_albums_table.setItem(row, 0, id_item)

            # Title
            title_item = QTableWidgetItem(album.get("title", ""))
            self.shared_albums_table.setItem(row, 1, title_item)

            # Items count
            count_item = QTableWidgetItem(str(album.get("mediaItemsCount", 0)))
            self.shared_albums_table.setItem(row, 2, count_item)

            # Writeable
            writeable_item = QTableWidgetItem("Yes" if album.get("isWriteable", False) else "No")
            self.shared_albums_table.setItem(row, 3, writeable_item)

        # Resize columns to content
        self.shared_albums_table.resizeColumnsToContents()

    def on_media_item_selected(self) -> None:
        """Handle media item selection to show details."""
        selected_items = self.media_items_table.selectedItems()
        if not selected_items:
            return

        # Get the first selected row's data
        row = selected_items[0].row()
        id_item = self.media_items_table.item(row, 0)
        if id_item:
            item_data = id_item.data(Qt.ItemDataRole.UserRole)
            if item_data:
                self._show_item_details(item_data, "Media Item")

    def on_album_selected(self) -> None:
        """Handle album selection to show details."""
        selected_items = self.albums_table.selectedItems()
        if not selected_items:
            return

        # Get the first selected row's data
        row = selected_items[0].row()
        id_item = self.albums_table.item(row, 0)
        if id_item:
            album_data = id_item.data(Qt.ItemDataRole.UserRole)
            if album_data:
                self._show_item_details(album_data, "Album")

    def on_shared_album_selected(self) -> None:
        """Handle shared album selection to show details."""
        selected_items = self.shared_albums_table.selectedItems()
        if not selected_items:
            return

        # Get the first selected row's data
        row = selected_items[0].row()
        id_item = self.shared_albums_table.item(row, 0)
        if id_item:
            album_data = id_item.data(Qt.ItemDataRole.UserRole)
            if album_data:
                self._show_item_details(album_data, "Shared Album")

    def _show_item_details(self, data: dict[str, Any], item_type: str) -> None:
        """Show detailed JSON view of the selected item and display image if available.

        Args:
            data: The item data dictionary
            item_type: Type of item (for display)
        """
        # Switch to details tab
        self.data_tabs.setCurrentIndex(3)  # Details tab is index 3

        # Format JSON with indentation
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self.details_text.setPlainText(f"{item_type} Details:\n\n{json_str}")
        except Exception as e:
            self.log.error("Failed to format details: %s", e)
            self.details_text.setPlainText(f"Error displaying {item_type} details:\n{e}")
        
        # Display image if this is a media item with a baseUrl
        if item_type == "Media Item":
            media_file = data.get("mediaFile", {})
            base_url = media_file.get("baseUrl")
            if base_url:
                self._load_and_display_image(base_url)
            else:
                self.image_label.setText("No image URL available")
                self.image_label.setPixmap(QPixmap())
        else:
            self.image_label.setText("No image (not a media item)")
            self.image_label.setPixmap(QPixmap())
    
    def _load_and_display_image(self, url: str) -> None:
        """Load and display an image from a URL.

        Args:
            url: The image URL to load
        """
        self.log.info("Loading image from URL: %s", url)
        self.image_label.setText("Loading image...")
        self.image_label.setVisible(True)
        
        def load_image(ctx: WorkContext) -> QPixmap | None:
            """Load image in background worker."""
            try:
                import requests
                ctx.progress(50, "Fetching image...")
                
                # Image URLs require authentication - get token from picker
                headers = {}
                if (
                    self.picker
                    and self.picker.credentials
                    and not self.picker.credentials.valid
                    and self.picker.credentials.expired
                    and self.picker.credentials.refresh_token
                ):
                    # Refresh token if needed
                    self.picker.credentials.refresh(requests.Request())
                
                if self.picker and self.picker.credentials and self.picker.credentials.token:
                    headers["Authorization"] = (
                        f"Bearer {self.picker.credentials.token}"
                    )
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                ctx.progress(90, "Loading image data...")
                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    ctx.progress(100, "Image loaded")
                    return pixmap
                else:
                    self.log.error("Failed to load image data into pixmap")
                    return None
            except Exception:
                self.log.exception("Failed to load image from URL: %s", url)
                return None
        
        def image_loaded(pixmap: QPixmap | None) -> None:
            """Display loaded image on main thread."""
            if pixmap and not pixmap.isNull():
                self.log.info(
                    "Image loaded, pixmap: %dx%d, label: %dx%d",
                    pixmap.width(),
                    pixmap.height(),
                    self.image_label.width(),
                    self.image_label.height(),
                )
                # Get label size, but use a reasonable default if not yet sized
                label_size = self.image_label.size()
                if label_size.width() == 0 or label_size.height() == 0:
                    # Label not sized yet, use a default size based on image aspect ratio
                    # But limit to reasonable maximum
                    max_width = 800
                    max_height = 600
                    img_width = pixmap.width()
                    img_height = pixmap.height()
                    if img_width > 0 and img_height > 0:
                        aspect = img_width / img_height
                        if aspect > 1:
                            # Landscape
                            label_size = QSize(max_width, int(max_width / aspect))
                        else:
                            # Portrait
                            label_size = QSize(int(max_height * aspect), max_height)
                    else:
                        label_size = QSize(max_width, max_height)
                
                # Scale image to fit label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
                # Adjust label size to match scaled pixmap to prevent stretching
                self.image_label.setFixedSize(scaled_pixmap.size())
            else:
                self.image_label.setText("Failed to load image")
                self.image_label.setPixmap(QPixmap())
                self.image_label.setFixedSize(QSize())  # Reset fixed size
        
        def image_error(msg: str) -> None:
            """Handle image load error on main thread."""
            self.image_label.setText(f"Error loading image: {msg}")
            self.image_label.setPixmap(QPixmap())
        
        # Load image in background worker
        req = WorkRequest(fn=load_image, on_done=image_loaded, on_error=image_error)
        self.pool.submit(req)