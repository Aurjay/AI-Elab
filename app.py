from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import os
import threading
import speech_recognition as sr

app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract-audio', methods=['POST'])
def extract_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    if file and allowed_file(file.filename):
        # Create a temporary file to store the video
        temp_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.root_path, temp_filename)
        file.save(temp_filepath)

        # Start audio extraction and text extraction threads
        audio_thread = threading.Thread(target=convert_video_to_audio, args=(temp_filepath,))
        audio_thread.start()

        # Return success message
        return jsonify({'message': 'Conversion in progress'})

    return jsonify({'error': 'Invalid file format'})

def convert_video_to_audio(video_filepath):
    # Extract audio using moviepy
    video = VideoFileClip(video_filepath)
    audio = video.audio

    # Save the extracted audio as audio.wav in the same directory
    output_filepath = os.path.join(app.root_path, 'audio.wav')
    audio.write_audiofile(output_filepath)

    # Clean up
    video.close()
    audio.close()

    # Perform text extraction
    text = convert_audio_to_text(output_filepath)

    # Save text in a text.txt file in the same directory
    text_filepath = os.path.join(app.root_path, 'text.txt')
    save_text_to_file(text, text_filepath)

def convert_audio_to_text(audio_filepath):
    r = sr.Recognizer()
    audio = sr.AudioFile(audio_filepath)

    with audio as source:
        audio_data = r.record(source)

    text = r.recognize_google(audio_data)
    return text

def save_text_to_file(text, filepath):
    with open(filepath, 'w') as file:
        file.write(text)

if __name__ == '__main__':
    app.run(port=5003)
