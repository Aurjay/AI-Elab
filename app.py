from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import os
import speech_recognition as sr
from pydub import AudioSegment

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

        # Extract audio using moviepy
        video = VideoFileClip(temp_filepath)
        audio = video.audio

        # Save the extracted audio in the same directory
        output_filename = os.path.splitext(temp_filename)[0] + '.mp3'
        output_filepath = os.path.join(app.root_path, output_filename)
        audio.write_audiofile(output_filepath, codec='libmp3lame')  # Use 'libmp3lame' codec

        # Clean up the temporary files
        video.close()
        audio.close()
        os.remove(temp_filepath)

        # Convert audio to text
        converted_filepath = convert_audio_format(output_filepath)
        text = convert_audio_to_text(converted_filepath)

        # Save text in a .txt file in the same directory
        text_filename = os.path.splitext(temp_filename)[0] + '.txt'
        text_filepath = os.path.join(app.root_path, text_filename)
        save_text_to_file(text, text_filepath)

        # Return the path of the extracted text file
        return jsonify({'message': 'Text extracted successfully', 'text_link': text_filepath})

    return jsonify({'error': 'Invalid file format'})

def convert_audio_format(audio_filepath):
    # Convert audio file to WAV format
    converted_filepath = os.path.splitext(audio_filepath)[0] + '.wav'
    audio = AudioSegment.from_file(audio_filepath)
    audio.export(converted_filepath, format='wav')
    return converted_filepath

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
