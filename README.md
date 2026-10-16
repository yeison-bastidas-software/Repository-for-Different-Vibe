# Different Vibe
A full-stack web application that applies **slowed** and **sped-up** audio effects to MP3
and WAV files, with adjustable intensity and an in-browser preview and download step. Built with Flask, Pydub and FFmpeg on the backend, and Jinja2, Bootstrap 5 and vanilla JavaScript on the frontend.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture and Project Structure](#architecture-and-project-structure)
- [How It Works](#how-it-works)
- [The Audio Engine](#the-audio-engine)
- [Security Considerations](#security-considerations)
- [Error Handling and Edge Cases](#error-handling-and-edge-cases)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Key Design Decisions and Challenges](#key-design-decisions-and-challenges)
- [Limitations and Future Improvements](#limitations-and-future-improvements)
- [Author](#author)

---

## Overview

"Slowed + Reverb" and "Sped Up" edits are among the most popular transformations in modern music culture, used by DJs, content creators and listeners alike. Most tools that produce them are either desktop-only digital audio workstations or closed-source mobile apps.

**Different Vibe** distills this workflow into a simple four-step web experience:

1. Upload an audio file (MP3 or WAV, up to 480 MB).
2. Choose an effect mode: **SLOW** (deep, atmospheric) or **SPEED** (energetic, hype).
3. Set the effect intensity with a slider from 0% to 100%.
4. Preview the result in an HTML5 player and download the processed file.

Although it was originally built as the final project for Harvard's CS50x course, the codebase has been refactored beyond that scope: the processing layer is isolated from the routing layer, uploads are renamed with UUIDs to make concurrent usage safe, and the frontend feedback loop was rebuilt so the progress bar reflects real server completion instead of a purely cosmetic animation.

---

## Features

- **Two distinct effect modes**
  - *Slow*: tempo and pitch reduced from 1.0x down to 0.7x at maximum intensity.
  - *Speed*: tempo and pitch increased from 1.0x up to 1.5x at maximum intensity.
- **Continuous intensity control.** A 0-100 slider maps linearly to the speed factor, so users can dial in subtle or extreme edits; 0% returns a faithful copy of the original.
- **Format preservation.** The output keeps the container and codec family of the input: upload an MP3, download an MP3; upload a WAV, download a WAV. No forced transcoding.
- **Descriptive output naming.** Results are named `<original>_<mode>.<ext>` (e.g. `track_speed.mp3`), so downloads are self-explanatory.
- **Client-side and server-side size validation.** Files larger than 480 MB are rejected before upload by JavaScript and again by Flask (`MAX_CONTENT_LENGTH`), with a friendly redirect back to the home page instead of a raw HTTP error page.
- **Progress feedback synchronized with the server.** The progress bar advances optimistically but caps at 90% until the backend actually finishes, then jumps to 100% and navigates to the result page. If the request fails, the button is re-enabled and the user is told to retry.
- **Session-scoped workflow.** Uploaded files are tracked through Flask server-side sessions; users cannot reach intermediate pages without a valid upload in their session.
- **Responsive dark UI.** Bootstrap 5 grid plus custom CSS (wine/black palette, entrance animations, hover states, per-mode accent colors) targeting both desktop and mobile.

---

## Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Backend framework | Flask | Routing, sessions, static/file serving |
| Audio processing | pydub | Decoding, sample-rate manipulation, export |
| Media engine | FFmpeg (system dependency) | Actual MP3/WAV encoding and decoding invoked by pydub |
| Templating | Jinja2 | Server-rendered HTML with a shared base layout |
| Frontend | Bootstrap 5, custom CSS, vanilla JavaScript | Responsive UI, slider binding, upload validation, progress feedback |
| Language | Python 3 | Application logic |

There is intentionally no database and no ORM in the current version: the application is stateless beyond the short-lived processing session. See [Limitations and Future Improvements](#limitations-and-future-improvements).

---

## Architecture and Project Structure

The project follows standard Flask conventions, separating route control, domain logic, templates and static assets:

```
different-vibe/
├── app.py              # Entry point: configuration and all HTTP routes
├── helpers.py          # Audio processing engine (framework-independent)
├── requirements.txt    # Python dependencies (flask, pydub)
├── README.md
├── templates/          # Jinja2 views
│   ├── layout.html     # Base template: navbar, Bootstrap, CSS/JS includes
│   ├── index.html      # Upload form + size-error alert
│   ├── choose.html     # Mode selection cards (SLOW / SPEED)
│   ├── edit.html       # Intensity slider, progress bar, fetch-based submit
│   └── result.html     # HTML5 audio preview + download button
├── uploads/            # (created at runtime, gitignored) incoming files
└── static/
    ├── style.css       # Dark theme, animations, per-mode accents
    ├── script.js       # File-name display, client-side size check, slider sync
    └── processed/      # (created at runtime, gitignored) results served to users
```

**Responsibility split:**

- `app.py` owns everything HTTP-related: configuration, session lifecycle, file storage paths, route guards, redirects and error handlers. It never touches audio samples directly.
- `helpers.py` owns the single domain operation, `process_audio(input_path, output_path, mode, percentage)`, and knows nothing about Flask. This makes the DSP core unit-testable and reusable outside the web context.
- Templates contain presentation only, with one deliberate exception described in [Key Design Decisions](#key-design-decisions-and-challenges).

---

## How It Works

The request lifecycle for a complete editing session:

```
Browser                     Flask                          helpers.py
   │
   │  POST /  (multipart audio file)
   ├─────────────►  index(): validate presence, rename to
   │                <uuid>.<ext>, save to uploads/,
   │                store ids in session
   │                redirect ──► /choose
   │
   │  GET /choose
   ├─────────────►  choose(): session guard, render cards
   │
   │  GET /edit?mode=slow|speed
   ├─────────────►  edit(): validate mode param, session
   │                guard, report file size, render slider
   │
   │  POST /process?mode=..&intensity=..   (fetch API)
   ├─────────────►  process(): resolve paths, build output
   │                name "<base>_<mode>.<ext>"
   │                     │  process_audio(...)
   │                     ├──────────────► decode -> resample
   │                     │                -> export (FFmpeg)
   │                     ◄── (success, format)
   │                clear session, redirect ──► /result
   │
   │  GET /result?filename=..&format=..
   ├─────────────►  result(): render player + download link
   │
   │  GET /download/<filename>
   ├─────────────►  download(): send_from_directory(as_attachment=True)
```

State between steps travels in the server-side session (`filename`, `original_name`), so internal storage names are never required in URLs except at the final, read-only download step.

---

## The Audio Engine

Both effects share one algorithm implemented in `helpers.py`: **frame-rate override**, i.e. reinterpretation of the segment's sample rate rather than time-stretching.

1. Decode the input according to its extension (`from_wav` / `from_mp3`).
2. Map intensity to a multiplicative factor:
   - Slow: `factor = 1.0 - (intensity / 100) * 0.3` → range `[1.0, 0.7]`
   - Speed: `factor = 1.0 + (intensity / 100) * 0.5` → range `[1.0, 1.5]`
3. Spawn a new `AudioSegment` from the same raw PCM data with `frame_rate * factor` as its declared frame rate. Playing identical samples at a different declared rate changes tempo and pitch together — exactly the aesthetic of the slowed/sped genres.
4. Reset the segment to the original frame rate so the export stays compatible with standard players.
5. Export in the same format as the input.

A short-circuit for `intensity == 0` exports the untouched audio, and the whole pipeline is wrapped in a `try/except` that returns `(False, None)` on any failure, letting the route layer decide how to respond (HTTP 500).

This design gives both modes a shared, artifact-free code path with roughly 40 lines of domain logic.

---

## Security Considerations

- **UUID-based filename sanitization.** Every upload is stored as `uuid4().hex + ext`. User-supplied names never touch the filesystem, which eliminates path traversal via the filename, collisions between concurrent users, and overwrite attacks. The original name is kept only inside the session and is used solely to derive the friendly output name.
- **Upload size limit enforced twice.** `MAX_CONTENT_LENGTH = 480 MB` aborts oversized bodies at the Flask layer; JavaScript performs the same check before the request even leaves the browser, saving bandwidth and giving instant feedback.
- **Strict input whitelisting.** The `mode` query parameter must be exactly `"slow"` or `"speed"` or the request is redirected; the file input restricts accepted extensions to `.mp3` and `.wav`; intensity is parsed as `int` with a default.
- **Safe file serving.** Downloads go through `send_from_directory()`, which confines resolution to the processed folder and refuses arbitrary paths, rather than exposing the filesystem through a hand-rolled handler.
- **Randomized secret key.** `SECRET_KEY` is generated with `os.urandom(32)` at startup, signing session cookies with entropy that is not hard-coded in the repository.
- **Session guards.** `/choose`, `/edit` and `/process` verify that a valid upload exists in the session before proceeding, preventing users from operating on files they did not just upload.

---

## Error Handling and Edge Cases

| Situation | Behavior |
|---|---|
| Missing or empty file in `POST /` | Redirect to home; no partial state written |
| Oversized upload | Custom `413` handler redirects to `/?error=size`; the template renders a styled alert |
| Oversized upload (detected early) | Client-side JS blocks submission and shows the limit inline |
| Tampered `mode` parameter | Validation rejects it and redirects to `/choose` |
| Direct navigation to `/choose`, `/edit`, `/process` without an upload | Session guard redirects to `/` |
| Corrupt or undecodable audio | `process_audio()` returns failure; route responds `500` instead of crashing |
| Progress request fails in the browser | Interval stopped, button re-enabled, visible "Error, try again" message |
| Processing completes | Session entries are popped so a stale file cannot be reprocessed |

---

## Getting Started

### Prerequisites

- Python 3.8 or newer
- **FFmpeg** installed system-wide (pydub shells out to it for MP3/WAV encoding and decoding)

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

### Installation

```bash
git clone https://github.com/YeisonBastidas/different-vibe.git
cd different-vibe
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running

```bash
python app.py
```

Open http://localhost:5000. The `uploads/` and `static/processed/` directories are created automatically on first run.

> Note: the app runs with Flask's development server and debug mode enabled. Before any real deployment, switch to a production WSGI server (e.g. Gunicorn) and set `debug=False`. See [Limitations](#limitations-and-future-improvements).

---

## API Reference

| Method | Route | Parameters | Description |
|---|---|---|---|
| GET / POST | `/` | `audio` (form file) | Landing page; accepts MP3/WAV uploads up to 480 MB |
| GET | `/choose` | — | Mode selection (session-guarded) |
| GET | `/edit` | `mode` ∈ {slow, speed} | Intensity slider page; reports file size |
| GET / POST | `/process` | `mode`, `intensity` (0-100) | Runs the transformation and clears the session |
| GET | `/result` | `filename`, `format` | Preview page with HTML5 player |
| GET | `/download/<filename>` | — | Attachment download of the processed file |

---

## Key Design Decisions and Challenges

**1. Replacing pydub's `speedup()` with frame-rate override.**
The obvious implementation for the Speed mode is pydub's built-in `speedup()`, but it produced inconsistent behavior and crashes on certain MP3 encodings, and it required a separate code path from the Slow mode. Reinterpreting the sample rate instead yields cleaner, artifact-free audio, unifies both modes under a single formula, and made the intensity slider trivial to map onto a continuous factor.

**2. From fake progress to honest progress.**
The first version animated the progress bar purely from the file size, which looked convincing but lied whenever processing finished early or failed. The current `edit.html` submits through the Fetch API, lets the bar crawl optimistically, clamps it at 90%, and only reaches 100% when the server response arrives — then navigates to `res.url`, which transparently follows the server-side redirect chain to the result page. Failure paths restore the UI instead of stranding the user on a stalled bar.

**3. Deliberate co-location of the submit logic in the template.**
During development, an external script consistently sent `mode=slow` regardless of the user's selection, due to browser caching of the static asset holding a stale mode value. The fix was architectural as much as practical: the mode now lives in a hidden input rendered by Jinja2, and the handler that reads it is embedded in the same response, so template state and script can never diverge. `script.js` retains only cache-insensitive concerns (slider label sync, client-side size check).

**4. Sessions over URL state.**
Passing the stored filename through the session rather than the query string keeps internal identifiers out of URLs and history, and centralizes the "does this user have a pending upload?" invariant in one place.

**5. Removing the database.**
Earlier iterations logged every transaction to SQLite. Once analytics were no longer a requirement, the persistence layer was deleted rather than left dormant: fewer moving parts, no schema migrations, no connection handling, and an application that is genuinely stateless between sessions. This trade-off is revisited under future improvements.

---

## Limitations and Future Improvements

Acknowledged limitations of the current version:

- Processing is synchronous: a long file blocks its worker for the duration of the transform. A task queue (Celery/RQ) with polling or WebSocket updates would decouple the two.
- Uploaded and processed files accumulate on disk and are never garbage-collected; a TTL cleanup job is needed for anything beyond local use.
- The dev server, debug mode, and per-boot `SECRET_KEY` (which invalidates sessions on restart) are appropriate for a portfolio demo, not for deployment behind multiple workers.
- Output filenames are derived from user-controlled text; server-side sanitization of the base name would harden the download route further.
- No automated test suite yet; `helpers.py`'s pure-function design makes unit testing straightforward and is the natural next step.

Planned enhancements: pitch-preservation option (time stretch without pitch shift), a "reverb" layer to complete the classic slowed + reverb sound, batch processing, and optional account-based history.

---

## Author

**Yeison Bastidas** — Software developer.

- Email: yeisonbastidassoftware@gmail.com
