# Google Photos Library API - Complete Data Reference

## Overview

The **Google Photos Library API** enables applications to interact with users' Google Photos libraries. Applications can upload media items, create albums, organize content, and access media items and albums that were created by the application.

**Important Update (March 31, 2025)**: The Library API now focuses on accessing and managing media items **uploaded by your application**. To access media items not uploaded by your app, use the [Google Photos Picker API](https://developers.google.com/photos/picker) instead.

**Language Support**: While Google provides official client libraries for Java and PHP, Python can be used through third-party libraries such as `google-photos-library-api` or `gphotospy`.

---

## Authorization

The API uses **OAuth 2.0** for authorization. Users must sign in with a valid Google Account. Service accounts are **not supported**.

### Required Scopes

- `https://www.googleapis.com/auth/photoslibrary.appendonly` - Upload media items and create albums
- `https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata` - Read media items and albums created by your application
- `https://www.googleapis.com/auth/photoslibrary` - Full access (read/write for app-created content)
- `https://www.googleapis.com/auth/photoslibrary.sharing` - Share albums and access shared albums

---

## API Resources

### 1. Media Items (`mediaItems`)

A `mediaItem` represents a photo or video in the user's Google Photos library. Media items can only be accessed if they were uploaded by your application.

#### Media Item Properties

| Property          | Type   | Description                                                    |
| ----------------- | ------ | -------------------------------------------------------------- |
| `id`              | string | Unique identifier for the media item (required)                |
| `description`     | string | User-provided description of the media item                    |
| `baseUrl`         | string | Base URL to access the media item's bytes (temporary, expires) |
| `productUrl`      | string | Link to view the media item in Google Photos                   |
| `mimeType`        | string | MIME type (e.g., `image/jpeg`, `video/mp4`)                    |
| `filename`        | string | Original filename of the media item                            |
| `mediaMetadata`   | object | Metadata specific to the media type (see below)                |
| `contributorInfo` | object | Information about who contributed the media item               |
| `filename`        | string | Original filename when uploaded                                |

#### Media Metadata (`mediaMetadata`)

Common metadata fields (applicable to both photos and videos):

| Property       | Type   | Description                                                 |
| -------------- | ------ | ----------------------------------------------------------- |
| `creationTime` | string | Timestamp when the media item was created (ISO 8601 format) |
| `width`        | string | Width of the media item in pixels                           |
| `height`       | string | Height of the media item in pixels                          |
| `photo`        | object | Photo-specific metadata (see below)                         |
| `video`        | object | Video-specific metadata (see below)                         |

#### Photo Metadata (`mediaMetadata.photo`)

Available when `mimeType` starts with `image/`:

| Property          | Type   | Description                                       |
| ----------------- | ------ | ------------------------------------------------- |
| `cameraMake`      | string | Camera manufacturer (e.g., "Canon", "Apple")      |
| `cameraModel`     | string | Camera model name                                 |
| `focalLength`     | number | Focal length of the lens in millimeters           |
| `apertureFNumber` | number | Aperture f-number (e.g., 2.8, 5.6)                |
| `isoEquivalent`   | number | ISO equivalent setting                            |
| `exposureTime`    | string | Exposure time in seconds (e.g., "0.004", "1/250") |

#### Video Metadata (`mediaMetadata.video`)

Available when `mimeType` starts with `video/`:

| Property | Type   | Description                                                        |
| -------- | ------ | ------------------------------------------------------------------ |
| `fps`    | number | Frames per second                                                  |
| `status` | string | Processing status (`UNSPECIFIED`, `PROCESSING`, `READY`, `FAILED`) |

#### Contributor Info (`contributorInfo`)

| Property                | Type   | Description                                    |
| ----------------------- | ------ | ---------------------------------------------- |
| `profilePictureBaseUrl` | string | Base URL for the contributor's profile picture |
| `displayName`           | string | Display name of the contributor                |

#### Base URL Parameters

When using `baseUrl` to access media bytes, you must append query parameters:

- `=d` - Download the media item
- `=w{width}` - Get a resized version with specified width (e.g., `=w500`)
- `=h{height}` - Get a resized version with specified height (e.g., `=h300`)
- `=w{width}-h{height}` - Get a resized version with both width and height (e.g., `=w500-h300`)
- `=c` - Get a cropped square version
- `=d-w{width}-h{height}` - Download a resized version

**Important**: Store media item IDs, not URLs, as `baseUrl` values expire.

---

### 2. Albums (`albums`)

An `album` is a collection of media items. Albums can only be accessed if they were created by your application.

#### Album Properties

| Property                | Type    | Description                                          |
| ----------------------- | ------- | ---------------------------------------------------- |
| `id`                    | string  | Unique identifier for the album                      |
| `title`                 | string  | Title of the album                                   |
| `productUrl`            | string  | Link to view the album in Google Photos              |
| `isWriteable`           | boolean | Whether the album can be modified by the application |
| `shareInfo`             | object  | Sharing information (if the album is shared)         |
| `mediaItemsCount`       | string  | Number of media items in the album                   |
| `coverPhotoBaseUrl`     | string  | Base URL for the cover photo                         |
| `coverPhotoMediaItemId` | string  | Media item ID of the cover photo                     |

#### Share Info (`shareInfo`)

Available when the album is shared:

| Property             | Type    | Description                                          |
| -------------------- | ------- | ---------------------------------------------------- |
| `sharedAlbumOptions` | object  | Options for the shared album                         |
| `shareableUrl`       | string  | URL that can be used to share the album              |
| `shareToken`         | string  | Token used for sharing operations                    |
| `isJoined`           | boolean | Whether the current user has joined the shared album |
| `isOwned`            | boolean | Whether the current user owns the album              |

---

### 3. Shared Albums (`sharedAlbums`)

Shared albums are albums that have been shared with other users.

#### Shared Album Properties

Similar to regular albums, but accessed through the `sharedAlbums` endpoints. Properties include:

- All properties from regular `albums`
- Additional sharing-specific information
- Information about who the album is shared with

---

## API Endpoints

### Media Items Endpoints

#### 1. `mediaItems.list`

Lists media items uploaded by your application.

**Endpoint**: `GET https://photoslibrary.googleapis.com/v1/mediaItems`

**Query Parameters**:

- `pageSize` (integer) - Maximum number of media items to return (default: 25, max: 100)
- `pageToken` (string) - Token for pagination
- `filters` (object) - Filters to apply (date range, media type, etc.)

**Response**: List of `mediaItem` objects with a `nextPageToken` for pagination

#### 2. `mediaItems.get`

Retrieves a specific media item by ID.

**Endpoint**: `GET https://photoslibrary.googleapis.com/v1/mediaItems/{mediaItemId}`

**Path Parameters**:

- `mediaItemId` (string) - The ID of the media item to retrieve

**Response**: Single `mediaItem` object

#### 3. `mediaItems.search`

Searches for media items based on filters.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/mediaItems:search`

**Request Body**:

- `albumId` (string) - Search within a specific album
- `pageSize` (integer) - Maximum results per page
- `pageToken` (string) - Pagination token
- `filters` (object) - Search filters:
  - `dateFilter` - Filter by date range
  - `contentFilter` - Filter by media type
  - `mediaTypeFilter` - Filter by media type (PHOTO, VIDEO)
  - `includeArchivedMedia` (boolean) - Include archived items
  - `excludeNonAppCreatedData` (boolean) - Exclude non-app-created data

**Response**: List of `mediaItem` objects

#### 4. `mediaItems:batchCreate`

Uploads and creates multiple media items.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate`

**Request Body**:

- Array of media item creation requests
- Each request includes:
  - `description` (string) - Description for the media item
  - `simpleMediaItem` (object) - Upload token and filename

**Response**: Array of created `mediaItem` objects or errors

---

### Albums Endpoints

#### 1. `albums.list`

Lists albums created by your application.

**Endpoint**: `GET https://photoslibrary.googleapis.com/v1/albums`

**Query Parameters**:

- `pageSize` (integer) - Maximum number of albums to return (default: 20, max: 50)
- `pageToken` (string) - Token for pagination

**Response**: List of `album` objects with a `nextPageToken` for pagination

#### 2. `albums.get`

Retrieves a specific album by ID.

**Endpoint**: `GET https://photoslibrary.googleapis.com/v1/albums/{albumId}`

**Path Parameters**:

- `albumId` (string) - The ID of the album to retrieve

**Response**: Single `album` object

#### 3. `albums.create`

Creates a new album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums`

**Request Body**:

- `album` (object):
  - `title` (string) - Title of the album

**Response**: Created `album` object

#### 4. `albums:addEnrichment`

Adds enrichment (like location or text) to an album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums/{albumId}:addEnrichment`

**Request Body**:

- `newEnrichmentItem` (object) - The enrichment to add (location, map, text, etc.)
- `albumPosition` (object) - Position in the album

**Response**: Enrichment item with ID

#### 5. `albums:batchAddMediaItems`

Adds multiple media items to an album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums/{albumId}:batchAddMediaItems`

**Request Body**:

- `mediaItemIds` (array of strings) - IDs of media items to add

**Response**: Results of the batch operation

#### 6. `albums:batchRemoveMediaItems`

Removes multiple media items from an album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums/{albumId}:batchRemoveMediaItems`

**Request Body**:

- `mediaItemIds` (array of strings) - IDs of media items to remove

**Response**: Results of the batch operation

---

### Shared Albums Endpoints

#### 1. `sharedAlbums.list`

Lists albums shared with the user.

**Endpoint**: `GET https://photoslibrary.googleapis.com/v1/sharedAlbums`

**Query Parameters**:

- `pageSize` (integer) - Maximum number of albums to return
- `pageToken` (string) - Token for pagination

**Response**: List of `album` objects

#### 2. `sharedAlbums.join`

Joins a shared album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/sharedAlbums:join`

**Request Body**:

- `shareToken` (string) - Token from the shared album URL

**Response**: `album` object

#### 3. `albums:share`

Shares an album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums/{albumId}:share`

**Request Body**:

- `sharedAlbumOptions` (object) - Options for sharing (isCollaborative, isCommentable)

**Response**: `shareInfo` object

#### 4. `albums:unshare`

Unshares an album.

**Endpoint**: `POST https://photoslibrary.googleapis.com/v1/albums/{albumId}:unshare`

**Response**: Empty response

---

## Search Filters

### Date Filter

Filters media items by creation date:

```json
{
  "dateFilter": {
    "ranges": [
      {
        "startDate": { "year": 2024, "month": 1, "day": 1 },
        "endDate": { "year": 2024, "month": 12, "day": 31 }
      }
    ],
    "dates": [{ "year": 2024, "month": 6, "day": 15 }]
  }
}
```

### Content Filter

Filters by content categories:

```json
{
  "contentFilter": {
    "includedContentCategories": ["PEOPLE", "PETS", "LANDSCAPES"],
    "excludedContentCategories": ["SCREENSHOTS"]
  }
}
```

**Content Categories**:

- `NONE`
- `LANDSCAPES`
- `RECEIPTS`
- `CITYSCAPES`
- `LANDMARKS`
- `SELFIES`
- `PEOPLE`
- `PETS`
- `WEDDINGS`
- `BIRTHDAYS`
- `DOCUMENTS`
- `TRAVEL`
- `ANIMALS`
- `FOOD`
- `SPORT`
- `NIGHT`
- `PERFORMANCES`
- `WHITEBOARDS`
- `SCREENSHOTS`
- `UTILITY`
- `ARTS`
- `CRAFTS`
- `FASHION`
- `HOUSES`
- `GARDENS`
- `FLOWERS`
- `HOLIDAYS`

### Media Type Filter

Filters by media type:

```json
{
  "mediaTypeFilter": {
    "mediaTypes": ["PHOTO", "VIDEO"]
  }
}
```

---

## Enrichment Types

When adding enrichments to albums, you can add:

- **Location Enrichment** - Add a location to an album
- **Map Enrichment** - Add a map showing album locations
- **Text Enrichment** - Add text/description to an album

---

## Usage Limits and Quotas

Be aware of the following limits:

- **Rate Limits**: The API has rate limits per user per project
- **Quota Limits**: Daily quotas apply to API usage
- **Pagination**: Use pagination tokens to retrieve large datasets
- **Base URLs**: Media item `baseUrl` values expire - store IDs instead

For current quota and limit information, refer to the [official documentation](https://developers.google.com/photos/library/guides/api-limits-quotas).

---

## Error Responses

Common error codes:

- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or invalid
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

---

## Best Practices

1. **Store Media Item IDs**: Don't store `baseUrl` values as they expire. Store media item IDs and regenerate URLs when needed.

2. **Use Pagination**: Always handle pagination when listing media items or albums.

3. **Handle Errors Gracefully**: Implement proper error handling for API responses.

4. **Respect Rate Limits**: Implement exponential backoff for rate limit errors.

5. **Cache When Appropriate**: Cache album and media item metadata to reduce API calls.

6. **Use Appropriate Scopes**: Request only the scopes your application needs.

---

## Python Libraries

While Google doesn't provide an official Python client library, you can use:

- **`google-photos-library-api`** - Third-party Python library
- **`gphotospy`** - Another third-party option
- **Direct REST API calls** - Using `requests` library with OAuth 2.0

Example using `requests`:

```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://photoslibrary.googleapis.com/v1/mediaItems',
    headers=headers,
    params={'pageSize': 25}
)

media_items = response.json()
```

---

## Additional Resources

- [Official API Documentation](https://developers.google.com/photos/library/guides/overview)
- [API Reference](https://developers.google.com/photos/library/reference/rest)
- [Getting Started Guide](https://developers.google.com/photos/library/guides/get-started-library)
- [OAuth 2.0 Setup](https://developers.google.com/photos/library/guides/authentication-authorization)
- [Google Photos Picker API](https://developers.google.com/photos/picker) (for accessing non-app-created media)

---

_Last Updated: 2026_
