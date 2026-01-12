"""Google Photos Picker API client.

The Picker API allows users to select photos from their Google Photos library
through a web-based picker interface. Unlike the Library API, this can access
all photos in the user's library, not just app-created content.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from google.oauth2.credentials import Credentials

# Picker API base URL
PICKER_API_BASE_URL = "https://photospicker.googleapis.com/v1"

# Session status values
SESSION_STATUS_UNSPECIFIED = "SESSION_STATUS_UNSPECIFIED"
SESSION_STATUS_ACTIVE = "SESSION_STATUS_ACTIVE"
SESSION_STATUS_COMPLETE = "SESSION_STATUS_COMPLETE"
SESSION_STATUS_EXPIRED = "SESSION_STATUS_EXPIRED"


class GooglePhotosPicker:
    """Client for Google Photos Picker API."""

    def __init__(self, credentials: Credentials, debug: bool = False) -> None:
        """Initialize the Picker API client.

        Args:
            credentials: OAuth 2.0 credentials with photospicker.mediaitems.readonly scope
            debug: If True, log detailed API request/response information
        """
        self.log = logging.getLogger(__name__)
        self.credentials = credentials
        self.debug = debug
        self.session = requests.Session()
        self._update_session_auth()

    def _update_session_auth(self) -> None:
        """Update session with current credentials."""
        if not self.credentials.valid:
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(requests.Request())
            else:
                raise ValueError("Credentials are invalid and cannot be refreshed")

        # Set Authorization header
        self.session.headers.update(
            {"Authorization": f"Bearer {self.credentials.token}"}
        )

    def create_session(
        self,
        feature_filter: list[str] | None = None,
        media_type_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new picker session.

        Args:
            feature_filter: List of features to filter by (e.g., ["FAVORITES"])
            media_type_filter: List of media types (e.g., ["PHOTO", "VIDEO"])

        Returns:
            Session object with pickerUri and sessionId
        """
        self._update_session_auth()

        request_body: dict[str, Any] = {}
        if feature_filter:
            request_body["featureFilter"] = {"includedFeatures": feature_filter}
        if media_type_filter:
            request_body["mediaTypeFilter"] = {
                "mediaTypes": media_type_filter
            }

        url = f"{PICKER_API_BASE_URL}/sessions"
        if self.debug:
            self.log.info("Creating picker session: %s", request_body)

        response = self.session.post(url, json=request_body, timeout=30)
        
        # Log response details for debugging
        if self.debug:
            self.log.info("Response status: %s", response.status_code)
            self.log.info("Response headers: %s", dict(response.headers))
            self.log.info("Response text: %s", response.text[:500])  # First 500 chars
        
        response.raise_for_status()
        session_data = response.json()

        if self.debug:
            self.log.info("Session created response: %s", session_data)
            self.log.info("Session ID: %s", session_data.get("id"))
            self.log.info("Picker URI: %s", session_data.get("pickerUri"))

        # Check for error in response
        if "error" in session_data:
            error_msg = session_data.get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"Picker API error: {error_msg}")

        # Validate required fields
        # Note: API returns "id" not "sessionId"
        if "id" not in session_data:
            raise RuntimeError(
                f"Invalid response from Picker API: missing id. "
                f"Response: {session_data}"
            )
        if "pickerUri" not in session_data:
            raise RuntimeError(
                f"Invalid response from Picker API: missing pickerUri. "
                f"Response: {session_data}"
            )

        return session_data

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get the status of a picker session.

        Args:
            session_id: The session ID returned from create_session

        Returns:
            Session object with current status
        """
        self._update_session_auth()

        url = f"{PICKER_API_BASE_URL}/sessions/{session_id}"
        if self.debug:
            self.log.info("Getting session status: %s", session_id)

        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        session_data = response.json()
        
        if self.debug:
            self.log.info("Session status response: %s", session_data)
            self.log.info("mediaItemsSet: %s", session_data.get("mediaItemsSet"))
            self.log.info("status: %s", session_data.get("status"))
        
        return session_data

    def delete_session(self, session_id: str) -> None:
        """Delete a picker session.

        Args:
            session_id: The session ID to delete
        """
        self._update_session_auth()

        url = f"{PICKER_API_BASE_URL}/sessions/{session_id}"
        if self.debug:
            self.log.info("Deleting session: %s", session_id)

        response = self.session.delete(url, timeout=30)
        response.raise_for_status()

    def get_selected_media_items(
        self, session_id: str, page_size: int = 100, page_token: str | None = None
    ) -> dict[str, Any]:
        """Get the media items selected in a completed session.

        Uses the Library API mediaItems.list endpoint with a custom header
        to specify the Picker session ID.

        Args:
            session_id: The session ID
            page_size: Maximum number of items to return
            page_token: Token for pagination

        Returns:
            Response containing mediaItems and nextPageToken
        """
        self._update_session_auth()
        
        # Try using the Picker API endpoint for listing media items
        # The Library API endpoint doesn't accept sessionId, so we need a different approach
        # According to docs, we should use the Library API but maybe with a different method
        # Let's try the Picker API base URL first
        url = f"{PICKER_API_BASE_URL}/mediaItems"
        params: dict[str, Any] = {
            "sessionId": session_id,
            "pageSize": min(page_size, 100),
        }
        if page_token:
            params["pageToken"] = page_token
        
        if self.debug:
            self.log.info(
                "Getting selected media items for session: %s (page_token: %s)",
                session_id[:8],
                "yes" if page_token else "no",
            )
            self.log.info("Request URL: %s", url)
            self.log.info("Request params: %s", params)

        response = self.session.get(url, params=params, timeout=30)
        
        if self.debug:
            self.log.info("Response status: %s", response.status_code)
            self.log.info("Response headers: %s", dict(response.headers))
            if response.status_code != 200:
                self.log.info("Response text: %s", response.text[:1000])
        
        response.raise_for_status()
        result = response.json()
        
        if self.debug:
            items_count = len(result.get("mediaItems", []))
            has_next = "nextPageToken" in result
            self.log.info(
                "Retrieved %d items (has_next_page: %s)", items_count, has_next
            )
            # Log full response for debugging when we get 0 items
            if items_count == 0:
                self.log.warning("Full API response (0 items): %s", result)
        
        return result

    def wait_for_session_completion(
        self,
        session_id: str,
        timeout: int = 300,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Wait for a session to complete and return the final session state.

        Args:
            session_id: The session ID to wait for
            timeout: Maximum time to wait in seconds (default 5 minutes)
            poll_interval: Time between status checks in seconds

        Returns:
            Final session object

        Raises:
            TimeoutError: If session doesn't complete within timeout
        """
        start_time = time.time()

        while True:
            session = self.get_session(session_id)
            # Check mediaItemsSet - when True, user has completed selection
            media_items_set = session.get("mediaItemsSet", False)
            status = session.get("status", SESSION_STATUS_UNSPECIFIED)

            # Session is complete when mediaItemsSet is True
            if media_items_set or status == SESSION_STATUS_COMPLETE:
                return session
            elif status == SESSION_STATUS_EXPIRED:
                raise RuntimeError("Session expired before completion")
            elif status == SESSION_STATUS_ACTIVE or not media_items_set:
                # Still active, continue polling
                if time.time() - start_time > timeout:
                    raise TimeoutError(
                        f"Session did not complete within {timeout} seconds"
                    )
                time.sleep(poll_interval)
            else:
                raise RuntimeError(f"Unknown session status: {status}")

    def get_all_selected_media_items(
        self, session_id: str, page_size: int = 100
    ) -> list[dict[str, Any]]:
        """Get all selected media items from a completed session (handles pagination).

        Args:
            session_id: The session ID
            page_size: Number of items per page

        Returns:
            List of all selected media items
        """
        all_items: list[dict[str, Any]] = []
        page_token: str | None = None
        max_pages = 100  # Safety limit to prevent infinite loops

        page_count = 0
        while page_count < max_pages:
            response = self.get_selected_media_items(
                session_id, page_size=page_size, page_token=page_token
            )
            items = response.get("mediaItems", [])
            all_items.extend(items)

            page_token = response.get("nextPageToken")
            
            # Stop pagination if:
            # 1. No next page token, OR
            # 2. Current page returned 0 items (even if there's a token, it's likely a bug)
            if not page_token:
                break
            
            if len(items) == 0:
                self.log.warning(
                    "Received 0 items but nextPageToken exists - stopping pagination "
                    "to prevent infinite loop"
                )
                break
            
            page_count += 1
            
            if self.debug:
                self.log.info(
                    "Pagination: page %d, items this page: %d, total items: %d",
                    page_count,
                    len(items),
                    len(all_items),
                )

        if page_count >= max_pages:
            self.log.warning(
                "Reached maximum page limit (%d) for session %s", max_pages, session_id[:8]
            )

        return all_items
