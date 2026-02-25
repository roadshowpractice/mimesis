# Caller/Library Status for SRT + Recent Activity

## Which caller and libraries to use for `.srt`

Use the local-media caller:

- `bin/transcribe_media.py`

This caller writes SRT when invoked with `--srt` and can also write `--vtt`,
`--minute-json`, plus default `--txt` and `--json` outputs.

Primary libraries involved in this path:

- `openai-whisper` (model loading + transcription)
- `ffmpeg` (required on PATH)
- Python stdlib helpers in the same caller for timestamp and SRT writing.

Legacy callers still exist but are marked legacy in project docs:

- `bin/call_whisper_transcribe.py`
- `bin/call_whisper.py`

## Last-couple-weeks activity (based on git history)

Window used: `git log --since='2 weeks ago'`.

### Callers touched

- `bin/transcribe_media.py`

### Libraries touched

- No `lib/` library files were touched in this window.

### Callers not touched

- `bin/call_captions.py`
- `bin/call_clips.py`
- `bin/call_download.py`
- `bin/call_instagram_download.py`
- `bin/call_watermark.py`
- `bin/call_whisper.py`
- `bin/call_whisper_transcribe.py`
- `bin/compare_sources.py`
- `bin/continue_tasks.py`
- `bin/create_yaml.py`
- `bin/dispatch.py`
- `bin/extract_article_text.py`
- `bin/notes_to_audio.py`
- `bin/organize_vault.py`

### Libraries not touched

All library files under `lib/` and `lib/mimesis/` were not touched in this
window.

## `call_download` vs `call_instagram_download` (what actually differs)

Beyond URL sanitization/host checks, the two callers run **different pipelines** and
therefore populate different fields.

### `bin/call_download.py` behavior

- Sanitizes as Facebook-style URL and detects host.
- Skips work if URL metadata already exists (`find_url_json`).
- Builds params with `download_path`, `cookie_path`, `url`, `host`, task metadata,
  and watermark config.
- Runs a post-download chain:
  - `downloader5.mask_metadata` (extracts/normalizes metadata such as
    `video_title`, `video_date`, `uploader`, `ext`, codecs, bitrate, etc.)
  - `downloader5.create_original_filename` (names output from uploader/date/ext)
  - `store_params_as_json`, backup copy, task output extension.
- Updates task output path in metadata (`perform_download`).

### `bin/call_instagram_download.py` behavior

- Sanitizes as Instagram URL and warns if host is not Instagram.
- Does **not** check existing metadata before download.
- Uses fixed output naming: `instagram_video.mp4` in dated folder.
- Calls only `downloader5.download_video(params)` then `store_params_as_json`.
- Does **not** call metadata normalization (`mask_metadata`) or
  filename generation from uploader/date (`create_original_filename`).

### Field-level consequence you were remembering

- In `call_download`, fields like `uploader`, `video_date`, and `ext` are extracted
  (via `mask_metadata`) and then used to construct the final filename.
- In `call_instagram_download`, those fields are not extracted by the caller path,
  so output remains the fixed `instagram_video.mp4` unless changed elsewhere.

So yes: the practical difference is not just URL checks; the general downloader path
runs metadata extraction + task bookkeeping, while the Instagram caller is a much
thinner direct-download wrapper.
