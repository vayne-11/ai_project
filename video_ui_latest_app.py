from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename
import os
import moviepy.editor as mp
import speech_recognition as sr
from pydub import AudioSegment
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure Azure OpenAI service
openai_endpoint = "YOUR_AZURE_OPENAI_ENDPOINT"
openai_key = "YOUR_AZURE_OPENAI_KEY"
openai_model = "YOUR_OPENAI_MODEL"

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(file_path)

    with audio_file as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

@app.route('/')
def index():
    return render_template('index.html', result=None)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'video-file' not in request.files:
        return redirect(request.url)

    file = request.files['video-file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract audio from video
        video = mp.VideoFileClip(file_path)
        audio_path = file_path.replace('.mp4', '.wav')
        video.audio.write_audiofile(audio_path)

        # Convert to WAV if not already
        if not audio_path.endswith('.wav'):
            audio = AudioSegment.from_file(audio_path)
            audio_path = audio_path.replace('.mp4', '.wav')
            audio.export(audio_path, format="wav")

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        # Perform sentiment analysis using Azure OpenAI
        sentiment_analysis = analyze_sentiment(transcript)

        return render_template('index.html', result=sentiment_analysis)

def analyze_sentiment(transcript):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}"
    }

    data = {
        "documents": [
            {
                "id": "1",
                "language": "en",
                "text": transcript
            }
        ]
    }

    response = requests.post(f"{openai_endpoint}/text/analytics/v3.1/sentiment", headers=headers, json=data)
    sentiment_response = response.json()
    
    if response.status_code == 200:
        sentiment = sentiment_response['documents'][0]['sentiment']
        return f"Sentiment analysis result: {sentiment}"
    else:
        return "Error in sentiment analysis"

if __name__ == '__main__':
    app.run(debug=True)
