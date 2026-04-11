# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-03-22

### Added
- Added OpenAI-compatible backend support for both CLI and web app.
- Added CLI backend selection via `-b/--backend` (`ollama` or `openai_compatible`).
- Added backend selector in the web UI connection settings.
- Added PDF layout-aware translation support (`.pdf` input to translated `.pdf` output).

### Changed
- Model query endpoint now supports both Ollama (`/api/tags`) and OpenAI-compatible (`/v1/models`) formats.
- Chat API calls now route to backend-specific endpoints (`/api/chat` or `/v1/chat/completions`).
- Response parsing now supports both Ollama and OpenAI-compatible response schemas.

## [1.3.0] - 2026-03-22

### Added
- Added Flask to `requirements.txt` to ensure the web GUI runs from a standard dependency install.
- Improved web UI file input with a styled upload control and selected filename display.

### Changed
- Redesigned the web upload page with a modern responsive layout and improved visual hierarchy.
- Simplified the Ollama connection success message to `✓ Connected!` (models remain in dropdown only).

### Fixed
- Fixed web form submission so the selected model is correctly posted to backend validation.
- Corrected Serbian Latin language code from `sr` to `sr-Latn` to avoid unintended Cyrillic output.

## [1.2.0] - 2026-03-21

### Added
- **Proofreading mode**: Automatic proofreading when source == target language, or force with `--proofread` flag
- **Optional API token**: Works without authentication for local Ollama instances
- New argument aliases: `-i/--input`, `-o/--output`, `-s/--source`, `-t/--target`, `-u/--url`

### Changed
- Renamed CLI arguments to more standard names (`--api-url` → `--url`)
- API token is now optional (previously required)
- Improved help text and argument descriptions

## [1.1.0] - 2026-03-21

### Added
- New `--api_url` argument that accepts base URL and automatically appends `/api/generate`
- Improved translation prompt with better instructions for preserving technical content
- Support for CPU-only Ollama instances (no GPU required)
- Test document creation script (`create_test_doc.py`)
- Web interface template (`templates/upload.html`)

### Changed
- Updated default API URL to `http://localhost:11434` (base URL only)
- Enhanced prompt engineering for professional translations similar to DeepL
- Better error handling and logging

### Fixed
- API endpoint construction now works with base URLs like `http://localhost:11434/`
- Improved language detection reliability
