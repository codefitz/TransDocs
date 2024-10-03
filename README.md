# TransDocs

This project provides a Python script and an untested web GUI for translating Microsoft Word documents (`.docx` files) from one language to another using the Ollama API. The script can automatically detect the source language based on a minimum of 50 words or accept a manually specified source language.

This script is currently not for Production scale workloads but can be used for personal translation tasks.

You need [Ollama](https://github.com/ollama/ollama) and/or [Open-WebUI](https://github.com/open-webui/open-webui) installed and setup with API ports configured.

- Default Ollama API URL: `http://<ollama-host>:11435/api/generate`
- Default Open-WebUI URL: `http://<open-webui-host>:3000/ollama/api/generate`

Speed depends on doc size and number of paragraphs. Running with Nvidia Titan-X with 24GB VRAM using the `glm4` model, estimated average of 1 page a minute.

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
  - [Web GUI Implementation (Untested)](#web-gui-implementation-untested)
    - [Setup](#setup)
    - [Running the Web App](#running-the-web-app)
  - [Logging](#logging)
    - [Adjusting Logging Levels](#adjusting-logging-levels)
  - [Troubleshooting](#troubleshooting)
  - [License](#license)

## Features

- **Automatic Source Language Detection**: Detects the source language by analyzing at least 50 words from the document.
- **Manual Source Language Specification**: Option to manually specify the source language using the `-s` or `--src_lang` argument.
- **Translation of All Document Elements**: Translates paragraphs, tables, headers, and footers within the document.
- **Detailed Logging**: Provides comprehensive logs to both console and file (`translation_debug.log`) for monitoring and debugging.
- **Web GUI Suggestion**: A suggested implementation using Flask for a user-friendly web interface to upload and translate documents.

## Requirements

- **Python**: Version 3.6 or higher.
- **Python Packages**:
  - `python-docx`
  - `requests`
  - `langdetect`
  - `flask` (for the web GUI)
  - `werkzeug` (for file handling in Flask)
- **Ollama API Access**: An API token for authenticating requests to the Ollama API.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/codefitz/TransDocs.git
   cd TransDocs
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install python-docx requests langdetect flask werkzeug
   ```

## Usage

### Command-Line Interface

The script `transdoc.py` can be executed from the command line to translate documents.

#### Arguments

- `-i`, `--input_file` (required): Path to the input Word document.
- `-o`, `--output_file` (required): Path to save the translated Word document.
- `-t`, `--target_lang` (required): Target language code (e.g., `en`, `de`, `fr`).
- `-k`, `--api_token` (required): Your Ollama API token for authentication.
- `-m`, `--model`: Model name to use for translation (e.g `llama3.2`).
- `-s`, `--src_lang`: Source language code (if not provided, the script will attempt to detect it).

#### Examples

1. **Translate a Document with Automatic Source Language Detection**

   ```bash
   python transdoc.py -i input.docx -o output.docx -t en -k your_api_token
   ```

   This command translates `input.docx` to English, saving the result as `output.docx`. The script will detect the source language automatically.

2. **Translate a Document with Specified Source Language**

   ```bash
   python transdoc.py -i input.docx -o output.docx -t en -k your_api_token -s fr
   ```

   This command translates `input.docx` from French to English.

3. **Translate Using a Specific Model**

   ```bash
   python transdoc.py -i input.docx -o output.docx -t en -k your_api_token -m custom_model
   ```

   This command uses `custom_model` instead of the default `llama3.2` for translation.

#### Running the Script

1. **Ensure All Dependencies Are Installed**

   ```bash
   pip install python-docx requests langdetect
   ```

2. **Execute the Script**

   ```bash
   python transdoc.py [arguments]
   ```

   Replace `[arguments]` with the appropriate command-line arguments as shown in the examples.

## Web GUI Implementation (Untested)

A web-based interface can enhance usability by allowing users to upload documents and receive translations without using the command line. Below is a suggested implementation using Flask.

### Setup

1. **Install Flask and Werkzeug**

   ```bash
   pip install flask werkzeug
   ```

### Running the Web App

1. **Start the Flask Application**

   ```bash
   python app.py
   ```

2. **Access the Web Interface**

   Open a web browser and navigate to `http://localhost:5000`.

3. **Upload and Translate**

   - **Upload Document**: Choose the `.docx` file you want to translate.
   - **Source Language**: Optionally enter the source language code.
   - **Target Language**: Enter the target language code.
   - **Model**: Optionally specify a different model.
   - **API Token**: Enter your Ollama API token.
   - **Translate**: Click the "Translate" button to start the translation process.

4. **Download the Translated Document**

   After the translation is complete, you'll be redirected to a page where you can download the translated document.

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
  - **API Token**: Verify that your Ollama API token is correct and has the necessary permissions.

- **Language Detection Fails**

  - **Insufficient Text**: The document may not have enough text (minimum 50 words) for language detection.
  - **Specify Source Language**: Use the `-s` option to manually specify the source language.

- **API Errors**

  - **Invalid API Token**: Ensure your API token is valid.
  - **Network Issues**: Check your internet connection.
  - **API Endpoint**: Verify that the API URL in the script is correct and accessible.

- **Output File Not Created**

  - **Permissions**: Ensure you have write permissions for the output directory.
  - **Exceptions**: Check `translation_debug.log` for any exceptions that may have occurred during processing.

- **Web App Issues**

  - **Port Already in Use**: If the web app doesn't start, the port may be in use. Change the port in `app.run()`:

    ```python
    app.run(debug=True, port=5001)
    ```

  - **File Upload Errors**: Ensure that the upload directory exists and has appropriate permissions.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the terms of the license.