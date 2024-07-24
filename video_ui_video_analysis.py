import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from utils import extract_frames, emotions_dict

# Load pre-trained emotion detection model
model = load_model('emotion_model.h5')

def analyze_video(video_path):
    # Extract frames from the video
    frames = extract_frames(video_path)

    emotions_count = {emotion: 0 for emotion in emotions_dict.values()}

    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, (48, 48))
            roi = roi.astype("float") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)

            preds = model.predict(roi)[0]
            emotion_probability = np.max(preds)
            emotion_label = emotions_dict[np.argmax(preds)]
            emotions_count[emotion_label] += 1

    # Determine the most common emotion
    most_common_emotion = max(emotions_count, key=emotions_count.get)

    return f"The most common emotion detected in the video is {most_common_emotion}."

