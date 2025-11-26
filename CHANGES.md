# Changes Made - Google Drive & Real-Debrid Integration

## Summary

Added automatic Google Drive upload and Real-Debrid unrestrict functionality to the N_m3u8DL-RE processor. After MP4 conversion, files are now:
1. Uploaded to Google Drive
2. Unrestricted via Real-Debrid API
3. Direct download link is returned in the job response

## Files Modified

### 1. `requirements.txt`
- Added `requests==2.32.3` for Real-Debrid API calls
- PyDrive2 was already present

### 2. `app.py`
**New Imports:**
- `requests` - For Real-Debrid API
- `GoogleAuth`, `GoogleDrive` from PyDrive2

**New Configuration:**
- `RD_API_KEY` - Real-Debrid API key
- `RD_API_BASE` - Real-Debrid API base URL

**New Functions:**
- `upload_to_google_drive(file_path)` - Uploads file to Google Drive and returns shareable link
- `unrestrict_with_real_debrid(gdrive_link)` - Unrestricts Google Drive link via Real-Debrid

**Modified Function:**
- `run_n_m3u8dl_process()` - Added Google Drive upload and Real-Debrid unrestrict after MP4 conversion

**New Job Statuses:**
- `uploading_to_gdrive` - Currently uploading to Google Drive
- `unrestricting_via_rd` - Currently unrestricting via Real-Debrid

**New Response Fields:**
- `gdrive_link` - Google Drive shareable link
- `rd_direct_link` - Real-Debrid direct download link
- `gdrive_error` - Error message if Google Drive upload fails
- `rd_error` - Error message if Real-Debrid unrestrict fails

### 3. `README.md`
- Updated with comprehensive documentation
- Added examples of API usage
- Documented new response fields
- Added setup instructions for Google Drive and Real-Debrid

## Files Created

### 1. `settings.yaml`
- PyDrive2 authentication configuration
- Uses client_secrets.json credentials
- Configures OAuth scopes for Google Drive

### 2. `example_usage.py`
- Example script showing how to use the API
- Demonstrates the complete workflow
- Includes health check example

## Testing Results

✅ **Google Drive Upload**: Successfully tested
- Uploaded test file to Google Drive
- Generated shareable link
- Link format: `https://drive.google.com/file/d/...`

✅ **Real-Debrid Unrestrict**: Successfully tested
- Successfully unrestricted Google Drive link
- Generated direct download link
- Link format: `https://chi3-4.download.real-debrid.com/d/...`

✅ **FastAPI Application**: Successfully tested
- Application starts without errors
- Health endpoint responding correctly
- All endpoints functional

## Workflow

1. User submits stream URL with decryption key via `/process` endpoint
2. N_m3u8DL-RE downloads and decrypts the stream
3. FFmpeg converts MKV to MP4
4. File is uploaded to Google Drive (status: `uploading_to_gdrive`)
5. Google Drive link is unrestricted via Real-Debrid (status: `unrestricting_via_rd`)
6. Job completes with both `gdrive_link` and `rd_direct_link` available

## API Response Example

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "my_video.mp4",
  "url": "/stream/my_video.mp4",
  "file_size_mb": 150.5,
  "converted_to_mp4": true,
  "gdrive_link": "https://drive.google.com/file/d/1dp9kEhZlqO9tX1NfNLzyutBpWaU_OfVU/view",
  "rd_direct_link": "https://chi3-4.download.real-debrid.com/d/T55WEUL6ZHPBG42/my_video.mp4"
}
```

## Deployment Notes

- First run requires Google Drive authentication via browser (local setup)
- Credentials are saved to `credentials.json` for subsequent runs
- Real-Debrid API key is hardcoded (consider environment variable for production)
- All operations are asynchronous and non-blocking
- Error handling in place for both Google Drive and Real-Debrid failures

## Security Considerations

- Real-Debrid API key is currently hardcoded
- Consider moving to environment variables for production
- Google Drive authentication uses OAuth2 with local credentials file

## Next Steps for Production

1. Move Real-Debrid API key to environment variable
2. Handle Google Drive quota limits
3. Add retry logic for network failures
4. Consider adding file cleanup after successful upload
5. Add logging for debugging

