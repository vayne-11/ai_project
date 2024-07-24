import cv2
import os

def extract_frames(video_path, frame_rate=1):
    vidcap = cv2.VideoCapture(video_path)
    frames = []
    success, image = vidcap.read()
    count = 0
    while success:
        if count % frame_rate == 0:
            frames.append(image)
        success, image = vidcap.read()
        count += 1
    return frames

# Emotion labels
emotions_dict = {0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy', 4: 'sad', 5: 'surprise', 6: 'neutral'}
