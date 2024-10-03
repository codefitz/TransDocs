from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from . import transdoc
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'outputs/'
ALLOWED_EXTENSIONS = {'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure the upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Get form data
        file = request.files['input_file']
        target_lang = request.form['target_lang']
        src_lang = request.form.get('src_lang', None)
        api_token = request.form['api_token']
        model = request.form.get('model', 'llama3.2')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_filename = f"translated_{filename}"
            output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            file.save(input_filepath)

            # Call your translation function here
            transdoc.process_document(input_filepath, output_filepath, model, target_lang, api_token, src_lang)

            return redirect(url_for('download_file', filename=output_filename))

    return render_template('upload.html')

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
