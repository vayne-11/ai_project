from flask import Flask, render_template, request, redirect, url_for
import base64
import os

app = Flask(__name__)

# Ensure the videos directory exists
if not os.path.exists('videos'):
    os.makedirs('videos')

@app.route('/')
def index():
    return render_template('test.html')

@app.route('/submit_test', methods=['POST'])
def submit_test():
    video_responses = {}
    for i in range(1, 6):
        video_data = request.form.get(f'video{i}')
        if video_data:
            video_responses[f'question_{i}'] = video_data

    # Save videos or process them further
    for question, video_data in video_responses.items():
        # Extract base64 part from data URL
        video_base64 = video_data.split(",")[1]
        video_bytes = base64.b64decode(video_base64)
        video_path = os.path.join('videos', f'{question}.webm')

        with open(video_path, 'wb') as f:
            f.write(video_bytes)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
