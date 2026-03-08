import cv2
import os
from datetime import datetime

class FrameExtractor:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root     = os.path.dirname(self.current_dir)
        self.output_dir  = os.path.join(project_root, 'uploads', 'frames')
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_frames(self, video_path, frame_interval=30, max_frames=50):
        frames = []

        if not os.path.exists(video_path):
            return frames

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames

        fps         = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        saved_count = 0

        while saved_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps if fps > 0 else 0
                filename  = f"frame_{saved_count:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.jpg"
                filepath  = os.path.join(self.output_dir, filename)
                cv2.imwrite(filepath, frame)
                frames.append({
                    'path':         filepath,
                    'frame_number': frame_count,
                    'timestamp':    timestamp,
                    'filename':     filename
                })
                saved_count += 1

            frame_count += 1

        cap.release()
        return frames

    def extract_key_frames(self, video_path, num_frames=10):
        frames = []

        if not os.path.exists(video_path):
            return frames

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0:
            cap.release()
            return frames

        interval = max(1, total_frames // num_frames)

        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                filename = f"keyframe_{i:06d}_{datetime.now().strftime('%H%M%S%f')}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                cv2.imwrite(filepath, frame)
                frames.append({
                    'path':         filepath,
                    'frame_number': i,
                    'filename':     filename
                })
                if len(frames) >= num_frames:
                    break

        cap.release()
        return frames

    def extract_by_time(self, video_path, time_seconds, interval_seconds=5):
        frames = []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames

        fps      = cap.get(cv2.CAP_PROP_FPS)
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps if fps > 0 else 0

        current_time = 0
        while current_time < duration and current_time <= time_seconds:
            frame_number = int(current_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if ret:
                filename = f"time_{current_time:.1f}s_{datetime.now().strftime('%H%M%S%f')}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                cv2.imwrite(filepath, frame)
                frames.append({
                    'path':     filepath,
                    'time':     current_time,
                    'filename': filename
                })

            current_time += interval_seconds

        cap.release()
        return frames