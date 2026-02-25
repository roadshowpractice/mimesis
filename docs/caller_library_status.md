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
