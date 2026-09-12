import os
import uuid
from flask import Flask, redirect, render_template, request, session, url_for, send_from_directory

from helpers import process_audio

app = Flask(__name__)

app.config["SECRET_KEY"] = "diferente-vibra-secret-key-2026"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["PROCESSED_FOLDER"] = "static/processed"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

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
    output_filename_base = f"processed_{session['filename']}"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_filename_base)

    success = process_audio(input_path, output_path, mode, intensity)

    if not success:
        return "Error processing audio", 500

    # Store both MP3 and WAV filenames in session
    session["mp3_filename"] = output_filename_base.replace('.mp3', '_output.mp3') if not output_filename_base.endswith('_output.mp3') else output_filename_base
    session["wav_filename"] = session["mp3_filename"].replace('_output.mp3', '_output.wav')

    session.pop("filename", None)
    session.pop("original_name", None)

    return redirect(url_for("result"))

@app.route("/result")
def result():
    mp3_filename = session.get("mp3_filename")
    wav_filename = session.get("wav_filename")
    if not mp3_filename or not wav_filename:
        return redirect("/")
    return render_template("result.html", mp3_filename=mp3_filename, wav_filename=wav_filename)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["PROCESSED_FOLDER"], filename, as_attachment=True)
