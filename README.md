# TransDocs

This project provides a Python tool for translating or proofreading documents (`.docx` and `.pdf`) using Ollama or OpenAI-compatible chat APIs. The script can automatically detect the source language based on a minimum of 50 words or accept a manually specified source language.

**Project Structure:**
```
TransDocs/
├── src/
│   ├── __init__.py       # Package initialization, exports main functions
│   └── transdoc.py       # Core translation logic
├── tests/
│   ├── test_transdoc.py  # Unit tests
│   └── __init__.py
├── transdoc_app.py       # Flask web application
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── ... (other files)
```

This script is currently not for Production scale workloads but can be used for personal translation tasks.

You can use [Ollama](https://github.com/ollama/ollama) locally, or any OpenAI-compatible provider exposing `/v1/chat/completions`.

- Default API URL for Ollama: `http://localhost:11434` (base URL, `/api/chat` is auto-appended)
- OpenAI-compatible base URLs are supported (`/v1/chat/completions` is auto-appended)
- Works with any model loaded in your Ollama instance
- **API token is optional** - works without authentication for local instances

Speed depends on doc size, number of paragraphs, and hardware. On CPU-only systems, expect slower performance (potentially minutes per page). GPU acceleration significantly improves speed.

## Table of Contents

- [TransDocs](#transdocs)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Command-Line Interface](#command-line-interface)
      - [Arguments](#arguments)
      - [Examples](#examples)
      - [Running the Script](#running-the-script)
    - [Web GUI](#web-gui)
  - [Testing](#testing)
  - [Logging](#logging)
    - [Adjusting Logging Levels](#adjusting-logging-levels)
  - [Troubleshooting](#troubleshooting)
  - [License](#license)

## Features

- **Automatic Source Language Detection**: Detects the source language by analyzing at least 50 words from the document.
- **Manual Source Language Specification**: Option to manually specify the source language using the `-s` or `--source` argument.
- **Translation of All Document Elements**: Translates paragraphs, tables, headers, and footers within the document.
- **PDF Layout-Aware Translation**: Translates `.pdf` files and outputs translated `.pdf` by preserving page geometry and text block positions.
- **Professional Translation Quality**: Enhanced prompts for DeepL-like quality translations that preserve technical content.
- **Automatic Proofreading Mode**: When source == target language, automatically runs in proofreading mode to fix grammar/spelling.
- **Explicit Proofreading Flag**: Use `--proofread` to force proofreading regardless of language match.
- **Flexible API Configuration**: Supports `ollama` and `openai_compatible` backends with automatic endpoint construction.
- **CPU Support**: Works on CPU-only systems (no GPU required).
- **Optional Authentication**: API token is optional for local Ollama instances without authentication requirements.
- **Detailed Logging**: Provides comprehensive logs to both console and file (`translation_debug.log`) for monitoring and debugging.
- **Web GUI**: Flask-based web interface for easy document upload and translation.
- **Model Query in Web GUI**: Query Ollama for available models and select from a dropdown before translating.
- **Serbian Script Support**: Distinct language codes for Serbian Latin (`sr-Latn`) and Cyrillic (`sr-Cyrl`).

## Requirements

- **Python**: Version 3.6 or higher.
- **Python Packages**:
  - `python-docx`
  - `requests`
  - `langdetect`
  - `flask` (for the web GUI)
  - `werkzeug` (for file handling in Flask)
- **Ollama**: Installed and running locally or on a remote server.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/sasakocic/TransDocs.git
   cd TransDocs
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Install Ollama and Load a Model**

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.2  # or any other model you prefer
   ```

## Usage

### Command-Line Interface

The script `src/transdoc.py` can be executed from the command line to translate or proofread documents.

#### Arguments

- `-i`, `--input FILE` (required): Path to the input Word document file.
- `-o`, `--output FILE` (required): Path to save the output Word document file.
- `-t`, `--target LANG` (required): Target language code (e.g., `en`, `de`, `fr`). Use same as source for proofreading mode.
- `-k`, `--api-token TOKEN`: API token for Ollama authentication (**optional**).
- `-m`, `--model MODEL`: Model name to use for translation/proofreading (**required**).
- `-s`, `--source LANG`: Source language code (e.g., `en`, `de`, `fr`). Auto-detected if not provided. Use same as target for proofreading mode.
- `--proofread`: Force proofreading mode regardless of language match.
- `-u`, `--url URL`: API base URL (default: `http://localhost:11434`). Endpoint is auto-appended based on backend.
- `-b`, `--backend {ollama,openai_compatible}`: Backend type (default: `ollama`).

#### Examples

1. **Translate a Document with Automatic Source Language Detection**

   ```bash
   python src/transdoc.py -i input.docx -o output.docx -t en
   ```

   This command translates `input.docx` to English, saving the result as `output.docx`. The script will detect the source language automatically. No API token required for local Ollama without authentication.

2. **Translate a Document with Specified Source Language**

   ```bash
   python src/transdoc.py -i input.docx -o output.docx -t en -s fr
   ```

   This command translates `input.docx` from French to English.

3. **Translate Using a Specific Model and API Token**

   ```bash
   python src/transdoc.py -i input.docx -o output.docx -t de -m llama3.2:latest -k your_api_token
   ```

   This command uses `llama3.2:latest` for translation to German with an API token.

4. **Translate Using a Remote Ollama Instance**

   ```bash
   python src/transdoc.py -i input.docx -o output.docx -t de -u http://192.168.1.50:11434/
   ```

   This command connects to a remote Ollama server at `http://192.168.1.50:11434/`. The script automatically appends `/api/chat`.

5. **Translate Using OpenAI-Compatible API**

   ```bash
   python src/transdoc.py -i input.docx -o output.docx -t de -m gpt-4o-mini -b openai_compatible -u https://api.example.com -k your_api_token
   ```

   This command targets an OpenAI-compatible endpoint and automatically appends `/v1/chat/completions`.

5. **Proofread a Document (Same Language)**

   ```bash
   python src/transdoc.py -i document.docx -o corrected.docx -s en -t en
   ```

   When source and target languages are the same, the script automatically runs in proofreading mode to fix grammar, spelling, and clarity issues.

6. **Force Proofreading Mode**

   ```bash
   python src/transdoc.py -i document.docx -o corrected.docx -s en -t de --proofread
   ```

   The `--proofread` flag forces proofreading mode even when source and target languages differ.

#### Running the Script

1. **Ensure All Dependencies Are Installed**

   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Execute the Script**

   ```bash
   python src/transdoc.py [arguments]
   ```

   Replace `[arguments]` with the appropriate command-line arguments as shown in the examples.

### Web GUI

A web-based interface is available via `transdoc_app.py`.

#### Running the Web App

1. **Start the Flask Application**

   ```bash
   python transdoc_app.py
   ```

2. **Access the Web Interface**

   Open a web browser and navigate to `http://localhost:5000`.

3. **Upload and Translate**

   - **Choose Backend**: Select `Ollama` or `OpenAI-compatible`.
   - **Query Models**: Enter API URL and click **Query** to load available models.
   - **Upload Document**: Choose a `.docx` or `.pdf` file you want to translate.
   - **Source Language**: Optionally select source language.
   - **Target Language**: Select target language.
   - **Model**: Select a model from the dropdown (required).
   - **API Token**: Enter your Ollama API token (optional).
   - **Translate**: Click the "Translate" button to start the translation process.

4. **Download the Translated Document**

   After the translation is complete, you'll be redirected to a page where you can download the translated document.

## Testing

Run the unit tests using pytest or unittest:

```bash
# Using pytest
pytest tests/

# Using unittest
python -m unittest discover tests/
```

The test suite covers:
- Language detection (English, German, insufficient text)
- API calls for translation and proofreading modes
- Error handling
- Paragraph processing
- CLI argument parsing

## Logging

The script logs detailed information to both the console and a file named `translation_debug.log`. Logging is set to the `DEBUG` level, capturing all levels of log messages.

- **Console Output**: Real-time feedback while the script is running.
- **Log File**: A persistent record of the script's execution, useful for troubleshooting.

### Adjusting Logging Levels

If you want to reduce the verbosity of the console output, you can adjust the logging level in the script:

```python
console_handler.setLevel(logging.INFO)  # Change DEBUG to INFO
```

## Troubleshooting

- **Script Does Not Execute or Exits Immediately**

  - **Check Logging Output**: Ensure that the logging level is set to `DEBUG` to capture all messages.
  - **Verify File Paths**: Ensure that the input file path is correct and the file exists.
  - **Check Dependencies**: Ensure all required Python packages are installed.
  - **API Token**: If using a remote Ollama instance, verify that your API token is correct and has the necessary permissions.

- **Language Detection Fails**

  - **Insufficient Text**: The document may not have enough text (minimum 50 words) for language detection.
  - **Specify Source Language**: Use the `-s` option to manually specify the source language.

- **API Errors**

  - **Invalid API Token**: Ensure your API token is valid (if required by your Ollama instance).
  - **Network Issues**: Check your internet connection and firewall settings.
  - **API Endpoint**: Verify that the API URL in the script is correct and accessible.
  - **Model Not Found**: Ensure the model you specified is loaded in Ollama (`ollama list`).

- **Output File Not Created**

  - **Permissions**: Ensure you have write permissions for the output directory.
  - **Exceptions**: Check `translation_debug.log` for any exceptions that may have occurred during processing.

- **Slow Performance (CPU-only)**

  - This is expected on CPU-only systems. Consider using a GPU-accelerated Ollama instance or smaller models for faster results.

- **Web App Issues**

  - **Port Already in Use**: If the web app doesn't start, the port may be in use. Change the port in `app.run()`:

    ```python
    app.run(debug=True, port=5001)
    ```

  - **File Upload Errors**: Ensure that the upload directory exists and has appropriate permissions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. You are free to use, modify, and distribute this software as per the terms of the license.
