"""
Flask web application for TransDocs - Document Translation and Proofreading Tool.
"""

import os
import logging
import secrets
import threading
import time
import uuid
from urllib.parse import urlparse
import requests as http_requests
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

# Import from the src package
from src.transdoc import process_document

logger = logging.getLogger(__name__)


def _int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer for %s=%r, using %s", name, value, default)
        return default


def _is_debug_mode():
    return os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}


def _allowed_api_hosts():
    configured = os.getenv("TRANSDOC_ALLOWED_API_HOSTS", "")
    if configured.strip():
        return {host.strip().lower() for host in configured.split(",") if host.strip()}
    return {"localhost", "127.0.0.1", "::1", "host.docker.internal"}


def validate_api_url(api_url):
    parsed = urlparse(api_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("API URL must be a valid http(s) URL")

    if parsed.hostname.lower() not in _allowed_api_hosts():
        raise ValueError(
            "API host is not allowed. Set TRANSDOC_ALLOWED_API_HOSTS to permit it."
        )

    return api_url.strip()


app = Flask(__name__, template_folder="templates")  # Templates in templates/ subfolder
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    if _is_debug_mode():
        app.secret_key = "dev-secret-key"
    else:
        app.secret_key = secrets.token_hex(32)
        logger.warning(
            "FLASK_SECRET_KEY is not set; using an ephemeral secret key for this process."
        )

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.abspath("uploads")
OUTPUT_FOLDER = os.path.abspath("outputs")
ALLOWED_EXTENSIONS = {"docx", "pdf"}
MAX_CONTENT_LENGTH = _int_env("TRANSDOC_MAX_UPLOAD_MB", 16) * 1024 * 1024
JOB_RETENTION_SECONDS = _int_env("TRANSDOC_JOB_RETENTION_SECONDS", 3600)
MAX_JOB_RECORDS = _int_env("TRANSDOC_MAX_JOB_RECORDS", 500)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Ensure the upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

TRANSLATION_JOBS = {}
TRANSLATION_JOBS_LOCK = threading.Lock()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_jobs(now=None):
    now = now or time.time()
    with TRANSLATION_JOBS_LOCK:
        expired_job_ids = [
            job_id
            for job_id, job in TRANSLATION_JOBS.items()
            if job.get("status") in {"done", "error"} and (now - job.get("updated_at", now) > JOB_RETENTION_SECONDS)
        ]
        for job_id in expired_job_ids:
            TRANSLATION_JOBS.pop(job_id, None)

        if len(TRANSLATION_JOBS) <= MAX_JOB_RECORDS:
            return

        removable_jobs = sorted(
            (
                (job.get("updated_at", 0), job_id)
                for job_id, job in TRANSLATION_JOBS.items()
                if job.get("status") in {"done", "error"}
            )
        )
        while len(TRANSLATION_JOBS) > MAX_JOB_RECORDS and removable_jobs:
            _, job_id = removable_jobs.pop(0)
            TRANSLATION_JOBS.pop(job_id, None)


def create_job_state(job_id, filename):
    cleanup_jobs()
    now = time.time()
    with TRANSLATION_JOBS_LOCK:
        TRANSLATION_JOBS[job_id] = {
            "id": job_id,
            "status": "queued",
            "message": "Queued",
            "error": None,
            "completed": 0,
            "total": 0,
            "percent": 0,
            "output_filename": filename,
            "created_at": now,
            "updated_at": now,
        }


def update_job_state(job_id, **updates):
    cleanup_jobs()
    with TRANSLATION_JOBS_LOCK:
        if job_id in TRANSLATION_JOBS:
            updates.setdefault("updated_at", time.time())
            if updates.get("status") in {"done", "error"}:
                updates.setdefault("finished_at", updates["updated_at"])
            TRANSLATION_JOBS[job_id].update(updates)


def get_job_state(job_id):
    cleanup_jobs()
    with TRANSLATION_JOBS_LOCK:
        job = TRANSLATION_JOBS.get(job_id)
        return dict(job) if job else None


def run_translation_job(
    job_id,
    input_filepath,
    output_filepath,
    output_filename,
    model,
    target_lang,
    api_token,
    src_lang,
    api_url,
    backend,
):
    try:
        update_job_state(job_id, status="running", message="Initializing translation")

        def progress_callback(completed, total, message):
            percent = int((completed / total) * 100) if total else 0
            update_job_state(
                job_id,
                completed=completed,
                total=total,
                percent=percent,
                message=message or f"Processing {completed}/{total}",
                status="running",
            )

        process_document(
            input_filepath,
            output_filepath,
            model,
            target_lang,
            api_token,
            src_lang,
            api_url=api_url,
            backend=backend,
            progress_callback=progress_callback,
        )

        if not os.path.exists(output_filepath):
            raise RuntimeError("Translation completed but output file was not created")

        update_job_state(
            job_id,
            status="done",
            message="Translation completed",
            completed=max(get_job_state(job_id).get("completed", 0), 1),
            total=max(get_job_state(job_id).get("total", 1), 1),
            percent=100,
            output_filename=output_filename,
        )
    except Exception as exc:
        update_job_state(
            job_id,
            status="error",
            error=str(exc),
            message="Translation failed",
        )


def build_models_endpoints(api_url, backend):
    """Build ordered model-list endpoint candidates for the selected backend."""
    base_url = api_url.rstrip("/")
    endpoints = []

    def add(url):
        if url not in endpoints:
            endpoints.append(url)

    if backend == "openai_compatible":
        if base_url.endswith(("/v1/models", "/models")):
            add(base_url)
        elif base_url.endswith("/v1"):
            add(f"{base_url}/models")
        else:
            add(f"{base_url}/v1/models")
        # Fallback for Ollama-style gateways
        if base_url.endswith("/api/tags"):
            add(base_url)
        else:
            add(f"{base_url}/api/tags")
        return endpoints

    # Default: ollama
    if base_url.endswith("/api/tags"):
        add(base_url)
    else:
        add(f"{base_url}/api/tags")
    # Fallback for OpenAI-compatible gateways
    if base_url.endswith(("/v1/models", "/models")):
        add(base_url)
    elif base_url.endswith("/v1"):
        add(f"{base_url}/models")
    else:
        add(f"{base_url}/v1/models")
    return endpoints


def extract_model_names(data):
    """Extract model names from either Ollama or OpenAI-compatible responses."""
    items = data.get("data", [])
    openai_models = [m.get("id") for m in items if isinstance(m, dict) and m.get("id")]
    if openai_models:
        return openai_models
    items = data.get("models", [])
    return [m.get("name") for m in items if isinstance(m, dict) and m.get("name")]


@app.errorhandler(413)
def request_entity_too_large(_error):
    message = f"Uploaded file is too large. Maximum size is {MAX_CONTENT_LENGTH // (1024 * 1024)} MB."
    if request.path == "/start_translation":
        return jsonify({"success": False, "error": message}), 413
    return (
        render_template(
            "upload.html",
            error=message,
            selected_backend=request.form.get("backend", "ollama").strip() or "ollama",
            selected_api_url=request.form.get(
                "api_url", "http://localhost:11434"
            ).strip(),
        ),
        413,
    )


@app.route("/query_ollama", methods=["POST"])  # backward-compatible endpoint name
@app.route("/query_models", methods=["POST"])
def query_models():
    """API endpoint to test backend connection and get available models."""
    api_url = request.form.get("api_url", "http://localhost:11434").strip()
    backend = request.form.get("backend", "ollama").strip() or "ollama"
    api_token = request.form.get("api_token", "").strip() or None
    if backend not in {"ollama", "openai_compatible"}:
        backend = "ollama"
    try:
        api_url = validate_api_url(api_url)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    models_urls = build_models_endpoints(api_url, backend)
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        headers["X-API-Key"] = api_token
        headers["api-key"] = api_token

    try:
        last_status = None
        last_text = ""
        for models_url in models_urls:
            response = http_requests.get(models_url, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                models = extract_model_names(data)
                return jsonify({"success": True, "models": models})
            last_status = response.status_code
            last_text = response.text[:500]
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"HTTP {last_status}",
                    "details": last_text,
                }
            ),
            400,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/start_translation", methods=["POST"])
def start_translation():
    file = request.files.get("input_file")
    target_lang = request.form.get("target_lang", "").strip()
    src_lang = request.form.get("src_lang", "").strip() or None
    api_token = request.form.get("api_token", "").strip() or None
    model = request.form.get("model", "").strip()
    backend = request.form.get("backend", "ollama").strip() or "ollama"
    api_url = request.form.get("api_url", "http://localhost:11434").strip()

    if backend not in {"ollama", "openai_compatible"}:
        backend = "ollama"
    try:
        api_url = validate_api_url(api_url)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    if not model:
        return jsonify({"success": False, "error": "Please select a valid model"}), 400
    if not target_lang:
        return jsonify({"success": False, "error": "Target language is required"}), 400
    if not file or not allowed_file(file.filename):
        return (
            jsonify(
                {"success": False, "error": "Please upload a valid .docx or .pdf file"}
            ),
            400,
        )

    filename = secure_filename(file.filename)
    job_id = uuid.uuid4().hex
    input_filename = f"{job_id}_{filename}"
    input_base_name = os.path.splitext(filename)[0]
    input_extension = os.path.splitext(filename)[1].lower()
    output_extension = ".pdf" if input_extension == ".pdf" else ".docx"
    output_filename = f"translated_{job_id}_{input_base_name}{output_extension}"
    input_filepath = os.path.join(app.config["UPLOAD_FOLDER"], input_filename)
    output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
    file.save(input_filepath)

    create_job_state(job_id, output_filename)

    worker = threading.Thread(
        target=run_translation_job,
        args=(
            job_id,
            input_filepath,
            output_filepath,
            output_filename,
            model,
            target_lang,
            api_token,
            src_lang,
            api_url,
            backend,
        ),
        daemon=True,
    )
    worker.start()

    return jsonify({"success": True, "job_id": job_id})


@app.route("/translation_status/<job_id>", methods=["GET"])
def translation_status(job_id):
    job = get_job_state(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404

    response = {
        "success": True,
        "status": job["status"],
        "message": job.get("message", ""),
        "error": job.get("error"),
        "completed": job.get("completed", 0),
        "total": job.get("total", 0),
        "percent": job.get("percent", 0),
    }
    if job["status"] == "done":
        response["download_url"] = url_for(
            "download_file", filename=job["output_filename"]
        )
    return jsonify(response)


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Check if this is a test connection action (for backward compatibility)
        if request.form.get("action") == "test":
            api_url = request.form.get("api_url", "http://localhost:11434").strip()
            backend = request.form.get("backend", "ollama").strip() or "ollama"
            api_token = request.form.get("api_token", "").strip() or None
            if backend not in {"ollama", "openai_compatible"}:
                backend = "ollama"
            try:
                api_url = validate_api_url(api_url)
            except ValueError as exc:
                return render_template(
                    "upload.html",
                    connection_result=f"✗ Connection failed!<br>Error: {str(exc)}",
                    connection_success=False,
                    selected_backend=backend,
                    selected_api_url=api_url,
                )
            models_urls = build_models_endpoints(api_url, backend)
            headers = {}
            if api_token:
                headers["Authorization"] = f"Bearer {api_token}"
                headers["X-API-Key"] = api_token
                headers["api-key"] = api_token

            try:
                model_names = []
                last_status = None
                for models_url in models_urls:
                    response = http_requests.get(models_url, headers=headers, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        model_names = extract_model_names(data)
                        break
                    last_status = response.status_code
                if model_names:
                    result = "✓ Connected!"
                    return render_template(
                        "upload.html",
                        connection_result=result,
                        connection_success=True,
                        selected_backend=backend,
                        selected_api_url=api_url,
                    )
                if last_status:
                    result = f"✗ Connection failed! HTTP {last_status}"
                    return render_template(
                        "upload.html",
                        connection_result=result,
                        connection_success=False,
                        selected_backend=backend,
                        selected_api_url=api_url,
                    )
                result = "✓ Connected! No models loaded. Load a model first."
                return render_template(
                    "upload.html",
                    connection_result=result,
                    connection_success=True,
                    selected_backend=backend,
                    selected_api_url=api_url,
                )
            except Exception as e:
                result = (
                    f"✗ Connection failed!<br>Error: {str(e)}<br><br>"
                    "Check URL, backend type, and API token if required."
                )
                return render_template(
                    "upload.html",
                    connection_result=result,
                    connection_success=False,
                    selected_backend=backend,
                    selected_api_url=api_url,
                )

        # Get form data for translation
        file = request.files.get("input_file")
        target_lang = request.form.get("target_lang", "").strip()
        src_lang = request.form.get("src_lang", "").strip() or None
        api_token = request.form.get("api_token", "").strip() or None
        model = request.form.get("model", "")
        backend = request.form.get("backend", "ollama").strip() or "ollama"
        if backend not in {"ollama", "openai_compatible"}:
            backend = "ollama"

        if not model:
            return render_template(
                "upload.html",
                error="Please select a valid model from the dropdown (query first)",
                selected_backend=backend,
                selected_api_url=request.form.get(
                    "api_url", "http://localhost:11434"
                ).strip(),
            )
        model = model.strip()

        api_url = request.form.get("api_url", "http://localhost:11434").strip()
        try:
            api_url = validate_api_url(api_url)
        except ValueError as exc:
            return render_template(
                "upload.html",
                error=str(exc),
                selected_backend=backend,
                selected_api_url=request.form.get(
                    "api_url", "http://localhost:11434"
                ).strip(),
            )

        logger.debug(f"Using backend '{backend}' with API base URL: {api_url}")

        if not target_lang:
            return render_template(
                "upload.html",
                error="Target language is required",
                selected_backend=backend,
                selected_api_url=api_url,
            )

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            input_base_name = os.path.splitext(filename)[0]
            input_extension = os.path.splitext(filename)[1].lower()
            output_extension = ".pdf" if input_extension == ".pdf" else ".docx"
            output_filename = f"translated_{input_base_name}{output_extension}"
            output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
            file.save(input_filepath)

            # Call your translation function here
            try:
                process_document(
                    input_filepath,
                    output_filepath,
                    model,
                    target_lang,
                    api_token,
                    src_lang,
                    api_url=api_url,
                    backend=backend,
                )
                return redirect(url_for("download_file", filename=output_filename))
            except Exception as e:
                return render_template(
                    "upload.html",
                    error=f"Error processing document: {str(e)}",
                    selected_backend=backend,
                    selected_api_url=api_url,
                )

        if not file or not allowed_file(file.filename):
            return render_template(
                "upload.html",
                error="Please upload a valid .docx or .pdf file",
                selected_backend=backend,
                selected_api_url=api_url,
            )

    return render_template(
        "upload.html",
        selected_backend="ollama",
        selected_api_url="http://localhost:11434",
    )


@app.route("/downloads/<filename>")
def download_file(filename):
    safe_filename = secure_filename(filename)
    if not safe_filename or safe_filename != filename:
        abort(404)
    return send_from_directory(
        app.config["OUTPUT_FOLDER"], safe_filename, as_attachment=True
    )


if __name__ == "__main__":
    import os

    debug = os.environ.get("FLASK_DEBUG", "0") != "0"
    host = os.environ.get(
        "FLASK_HOST", "0.0.0.0"
    )  # Default to all interfaces for LAN access
    app.run(host=host, debug=debug)
