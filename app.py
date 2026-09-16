import os
import uuid
from flask import Flask, redirect, render_template, request, session, url_for, send_from_directory

from helpers import process_audio

app = Flask(__name__)

app.config["SECRET_KEY"] = os.urandom(32).hex()
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["PROCESSED_FOLDER"] = "static/processed"
app.config["MAX_CONTENT_LENGTH"] = 480 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PROCESSED_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "audio" not in request.files:
            return redirect("/")
        file = request.files["audio"]
        if file.filename == "":
            return redirect("/")

        original_filename = file.filename
        unique_id = uuid.uuid4().hex
        file_ext = os.path.splitext(original_filename)[1]
        secure_filename = f"{unique_id}{file_ext}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename))

        session["filename"] = secure_filename
        session["original_name"] = original_filename

        return redirect(url_for("choose"))

    return render_template("index.html")

@app.route("/choose")
def choose():
    if "filename" not in session:
        return redirect("/")
    return render_template("choose.html")

@app.route("/edit")
def edit():
    mode = request.args.get("mode")
    if mode not in ["slow", "speed"]:
        return redirect("/choose")
    if "filename" not in session:
        return redirect("/")

    filename = session["filename"]
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    except:
        file_size_mb = 1

    return render_template("edit.html", mode=mode, file_size_mb=file_size_mb)

@app.route("/process")
def process():
    mode = request.args.get("mode")
    intensity = request.args.get("intensity", 50, type=int)

    if "filename" not in session:
        return redirect("/")

    input_path = os.path.join(app.config["UPLOAD_FOLDER"], session["filename"])
    
    # Get original filename and extension
    original_name = session["original_name"]
    base_name = os.path.splitext(original_name)[0]
    file_ext = os.path.splitext(original_name)[1].lower()
    
    # Create output filename with effect name and same extension
    effect_suffix = "_slow" if mode == "slow" else "_speed"
    output_filename = f"{base_name}{effect_suffix}{file_ext}"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename)

    success, output_format = process_audio(input_path, output_path, mode, intensity)

    if not success:
        return "Error processing audio", 500

    session.pop("filename", None)
    session.pop("original_name", None)

    return redirect(url_for("result", filename=output_filename, format=output_format))

@app.route("/result")
def result():
    filename = request.args.get("filename")
    audio_format = request.args.get("format", "mp3")
    if not filename:
        return redirect("/")
    return render_template("result.html", filename=filename, audio_format=audio_format)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["PROCESSED_FOLDER"], filename, as_attachment=True)

@app.errorhandler(413)
def file_too_large(e):
    # Redirect home with error flag instead of white error page
    return redirect(url_for("index", error="size"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)