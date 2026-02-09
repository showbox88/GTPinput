# Changelog

## [Unreleased]

### Added
- **Persistent Login ("Remember Me")**: Added a checkbox on the login page to cache session tokens locally (`.session_cache`), allowing users to stay logged in across browser refreshes.
- **Manual Data Refresh**: Added a "Refresh Data" button to the Dashboard tab to force clear the cache and reload data from Supabase.
- **Chat UI Enhancements**:
    - Replaced the global full-screen spinner with an inline "Thinking..." indicator.
    - Added a custom CSS spinning halo animation for the thinking indicator.
    - Improved login/signup UX by wrapping inputs in `st.form` to support "Enter" key submission.
- **Data Sorting**: Dashboard now sorts records by Date (descending) and ID (descending) to ensure latest entries appear first.

### Fixed
- **OpenAI API Integration**: Resolved `400 Bad Request` error by adding `additionalProperties: false` to the JSON schema for Structured Outputs.
- **Supabase Deployment**: Fixed a typo in the secret name (`OPENAPI_API_KEY` -> `OPENAI_API_KEY`) that prevented the Edge Function from accessing the key.

### Changed
- **Dependencies**: None.
- **Configuration**: User now needs to set `OPENAI_API_KEY` in Supabase secrets.
