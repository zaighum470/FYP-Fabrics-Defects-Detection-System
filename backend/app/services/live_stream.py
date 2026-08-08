import cv2
import threading
import requests
import numpy as np
import time
import queue
import os
from ultralytics import YOLO
from ..config import MEDIUM_MODEL, NANO_MODEL, ESP32_URL, CLASS_NAMES, CLASS_COLORS
from ..database import SessionLocal


class LiveStreamManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.model = None
        self.class_names = CLASS_NAMES
        self.esp32_url = ESP32_URL

        self._source_type = "esp32"
        self._model_name = "medium"
        self._local_video_path = None
        self._user_id = None

        self.bytes_data = bytes()
        self.raw_frame = None
        self.detected_frame = None
        self.lock = threading.Lock()
        self.running = False

        self.frame_queue = queue.Queue(maxsize=3)
        self._jpeg_buffer = None
        self._jpeg_lock = threading.Lock()

        self.fps = 0
        self._fps_lock = threading.Lock()
        self._display_frame_times = []

        self._last_defect = None
        self._defect_count = 0
        self._defect_count_lock = threading.Lock()

        self._esp32_connected = False
        self._esp32_fail_count = 0
        self._auto_fallback_done = False
        self._local_connected = False

        self.capture_thread = None
        self.inference_thread = None
        self.display_thread = None

        # Database session for storing pending defects
        self._db_session = None

        self._initialized = True

    def set_user_id(self, user_id):
        """Set the user ID for storing defects"""
        self._user_id = user_id

    def get_user_id(self):
        """Get the current user ID"""
        return self._user_id

    @classmethod
    def get_instance(cls):
        return cls()

    def load_model(self, model_name="medium"):
        model_path = MEDIUM_MODEL if model_name == "medium" else NANO_MODEL
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        self.model = YOLO(model_path)
        self._model_name = model_name

    def start(self, source="esp32", model="medium"):
        if self.running:
            self.stop()

        self.load_model(model)

        # Create a new database session for this stream
        self._db_session = SessionLocal()

        self._source_type = source
        self._esp32_fail_count = 0
        self._auto_fallback_done = False
        self._esp32_connected = False
        self._local_connected = False
        self.bytes_data = bytes()

        if source == "local":
            self._find_local_video()

        self.running = True

        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.inference_thread = threading.Thread(target=self._run_inference, daemon=True)
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)

        self.capture_thread.start()
        self.inference_thread.start()
        self.display_thread.start()

    def stop(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.inference_thread:
            self.inference_thread.join(timeout=2)
        if self.display_thread:
            self.display_thread.join(timeout=2)

        # Close the database session
        if self._db_session is not None:
            self._db_session.close()
            self._db_session = None

    def _find_local_video(self):
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        for name in ["fabric.mp4", "video23.mp4", "faults.mp4"]:
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                self._local_video_path = candidate
                return

    def _capture_frames(self):
        local_cap = None
        reconnect_delay = 1

        while self.running:
            if self._source_type == "esp32":
                if local_cap is not None:
                    local_cap.release()
                    local_cap = None

                try:
                    stream = requests.get(self.esp32_url, stream=True, timeout=(3, 30), verify=False)
                    self._esp32_connected = True
                    self._esp32_fail_count = 0
                    reconnect_delay = 1

                    for chunk in stream.iter_content(chunk_size=65536):
                        if not self.running:
                            break
                        self.bytes_data += chunk

                        while True:
                            a = self.bytes_data.find(b'\xff\xd8')
                            b = self.bytes_data.find(b'\xff\xd9', a + 2 if a != -1 else 0)
                            if a != -1 and b != -1:
                                jpg = self.bytes_data[a:b+2]
                                self.bytes_data = self.bytes_data[b+2:]
                                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                                if img is not None:
                                    with self.lock:
                                        self.raw_frame = img
                                    try:
                                        self.frame_queue.put(img, block=False)
                                    except queue.Full:
                                        pass
                            else:
                                break

                    stream.close()
                    self._esp32_connected = False

                except Exception as e:
                    self._esp32_connected = False
                    self._esp32_fail_count += 1
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 10)

                    if not self._auto_fallback_done and self._esp32_fail_count >= 3:
                        self._auto_fallback_to_local()

            elif self._source_type == "local":
                if local_cap is None and self._local_video_path:
                    local_cap = cv2.VideoCapture(self._local_video_path)
                    self._local_connected = True

                if local_cap is not None:
                    success, frame = local_cap.read()
                    if not success:
                        local_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        success, frame = local_cap.read()
                        if not success:
                            self._local_connected = False
                            time.sleep(0.03)
                            continue

                    self._local_connected = True
                    with self.lock:
                        self.raw_frame = frame
                    try:
                        self.frame_queue.put(frame.copy(), block=False)
                    except queue.Full:
                        pass
                    time.sleep(1 / 30)

    def _auto_fallback_to_local(self):
        self._find_local_video()
        if self._local_video_path:
            self._source_type = "local"
            self._esp32_connected = False
            self._auto_fallback_done = True

    def _run_inference(self):
        while self.running:
            try:
                img = self.frame_queue.get(timeout=1.0)
                results = self.model(img, imgsz=256, conf=0.4, verbose=False)
                detections_this_frame = []

                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        if cls < len(self.class_names):
                            name = self.class_names[cls]
                            color = CLASS_COLORS[name]
                            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(img, f"{name} {conf:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            detections_this_frame.append({
                                "name": name,
                                "conf": conf,
                                "bbox": [x1, y1, x2, y2]
                            })

                if detections_this_frame:
                    with self._defect_count_lock:
                        self._last_defect = detections_this_frame[-1]["name"]
                        self._defect_count += len(detections_this_frame)
                    # Store defects to pending table with user_id
                    self._store_pending_defects(detections_this_frame)

                with self.lock:
                    self.detected_frame = img

            except queue.Empty:
                continue
            except Exception as e:
                time.sleep(0.1)

    def _store_pending_defects(self, detections):
        """Store detected defects to pending table via database session"""
        # Use the stream's database session if available, otherwise create a temporary one
        db = self._db_session
        temporary = False
        if db is None:
            db = SessionLocal()
            temporary = True
        try:
            from ..models.pending_defect import PendingDefect
            for det in detections:
                pending = PendingDefect(
                    defect_type=det["name"],
                    confidence=det["conf"],
                    bbox_x1=det["bbox"][0],
                    bbox_y1=det["bbox"][1],
                    bbox_x2=det["bbox"][2],
                    bbox_y2=det["bbox"][3],
                    user_id=self._user_id
                )
                db.add(pending)
            db.commit()
        except Exception as e:
            if db:
                db.rollback()
            # Silently ignore storage errors to not disrupt streaming
        finally:
            if temporary and db:
                db.close()

    def _display_loop(self):
        last_encoded_frame = None
        while self.running:
            try:
                with self.lock:
                    frame = self.detected_frame
                if frame is None:
                    time.sleep(0.01)
                    continue
                if frame is last_encoded_frame:
                    time.sleep(0.001)
                    continue

                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
                jpeg_bytes = buffer.tobytes()

                with self._jpeg_lock:
                    self._jpeg_buffer = jpeg_bytes

                now = time.time()
                with self._fps_lock:
                    self._display_frame_times.append(now)
                    self._display_frame_times = self._display_frame_times[-30:]
                    if len(self._display_frame_times) >= 2:
                        elapsed = self._display_frame_times[-1] - self._display_frame_times[0]
                        self.fps = len(self._display_frame_times) / elapsed if elapsed > 0 else 0

                last_encoded_frame = frame
            except Exception as e:
                time.sleep(0.01)

    def get_frame(self):
        with self._jpeg_lock:
            return self._jpeg_buffer

    def get_raw_frame(self):
        with self.lock:
            if self.raw_frame is None:
                return None
            _, buffer = cv2.imencode(".jpg", self.raw_frame)
            return buffer.tobytes()

    def get_fps(self):
        with self._fps_lock:
            return self.fps

    def get_defect_count(self):
        with self._defect_count_lock:
            return self._defect_count

    def get_last_defect_name(self):
        with self._defect_count_lock:
            return self._last_defect

    def is_running(self):
        return self.running

    def get_source(self):
        return self._source_type

    def is_esp32_connected(self):
        return self._esp32_connected and self._source_type == "esp32"

    def is_local_connected(self):
        return self._local_connected and self._source_type == "local"
