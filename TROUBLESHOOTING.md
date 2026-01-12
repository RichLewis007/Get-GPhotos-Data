# Troubleshooting Guide

## 403 Forbidden Error

If you get a `403 Client Error: Forbidden` when trying to refresh data, this usually indicates one of these issues:

### 1. Google Photos Library API Not Enabled

**Symptom**: 403 error when trying to access any API endpoint

**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** > **Library**
4. Search for "Google Photos Library API"
5. Click on it and click **Enable**
6. Wait a few minutes for the API to be enabled
7. Try refreshing data again

### 2. OAuth Scope Not Added to Consent Screen

**Symptom**: Authentication works, but API calls return 403

**Solution**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** > **OAuth consent screen**
4. Click **Edit App**
5. Scroll down to **Scopes**
6. Click **Add or Remove Scopes**
7. Search for and add: `https://www.googleapis.com/auth/photoslibrary.readonly`
8. Click **Update**
9. **Re-authenticate** in the application (delete the token file or click "Re-authenticate")

### 3. Scope Not Granted During Authentication

**Symptom**: You authenticated but didn't see the scope permission request

**Solution**:
1. Delete the token file (located in your app data directory)
   - On macOS: `~/Library/Application Support/get-gphotos-data/google_photos_token.json`
   - On Windows: `%APPDATA%\get-gphotos-data\google_photos_token.json`
   - On Linux: `~/.config/get-gphotos-data/google_photos_token.json`
2. Re-authenticate in the application
3. Make sure to click "Allow" when prompted for Google Photos access

### 4. Test Users (For External Apps in Testing Mode)

**Symptom**: 403 error even after following steps 1-3

**Solution**:
1. Go to **OAuth consent screen** in Google Cloud Console
2. Under **Test users**, add your Google account email
3. Re-authenticate in the application

### Quick Checklist

- [ ] Google Photos Library API is enabled in Google Cloud Console
- [ ] OAuth scope `photoslibrary.readonly` is added to consent screen
- [ ] You've re-authenticated after making changes
- [ ] Your Google account is added as a test user (if app is in testing mode)
- [ ] You granted all permissions during the OAuth flow

## Other Common Issues

### "Credentials file not found"

- Make sure you've downloaded the OAuth credentials JSON file from Google Cloud Console
- Place it in the project root directory or select it when prompted

### "Failed to authenticate"

- Check your internet connection
- Verify the credentials file is valid JSON
- Make sure you're using a Desktop app OAuth client ID (not Web application)

### No data shown after successful authentication

- Remember: The Library API only shows media items/albums created by your application
- If you haven't uploaded anything via the API, you won't see any media items
- Use "Refresh Data" to fetch the latest data

### Token refresh issues

- Delete the token file and re-authenticate
- Check that your OAuth credentials are still valid in Google Cloud Console
