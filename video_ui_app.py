from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from video_analysis import analyze_video

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'video-file' not in request.files:
        return jsonify({'result': 'No file part'})

    file = request.files['video-file']

    if file.filename == '':
        return jsonify({'result': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Perform sentiment and emotion analysis
        result = analyze_video(file_path)

        return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True)
