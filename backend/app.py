from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
from datetime import datetime
from PIL import Image
from io import BytesIO
import threading
import os
import time
import sys

# Cargar variables de entorno
load_dotenv()

SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX = (3, 12)


def validate_python_version():
    current = sys.version_info[:2]
    if SUPPORTED_PYTHON_MIN <= current <= SUPPORTED_PYTHON_MAX:
        return
    version_str = f"{current[0]}.{current[1]}"
    print(
        "ADVERTENCIA: Esta version de Python "
        f"({version_str}) no esta oficialmente validada para este proyecto. "
        "Se recomienda usar Python 3.10, 3.11 o 3.12."
    )

# -----------------------------
# CONFIGURACIÓN DE LA APP
# -----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta_segura')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

MODEL_PATH = "models/best.pt"
CONFIDENCE_THRESHOLD = 0.5
MAX_HISTORY = 50
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
DANGEROUS_LABELS = {"gun", "knife", "arma", "pistola", "cuchillo"}

model = None
camera = None
is_running = False
lock = threading.Lock()

# -----------------------------
# TRACKER
# -----------------------------
class DetectionTracker:
    def __init__(self):
        self.history = deque(maxlen=MAX_HISTORY)

    def add_detection(self, class_name, confidence, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        detection = {
            'class': class_name,
            'confidence': round(float(confidence), 2),
            'timestamp': timestamp
        }
        self.history.append(detection)
        return detection

    def get_history(self):
        return list(self.history)

    def clear_history(self):
        self.history.clear()

tracker = DetectionTracker()

def load_model():
    global model
    try:
        if os.path.exists(MODEL_PATH):
            print(f"Cargando modelo desde {MODEL_PATH} ...")
            model = YOLO(MODEL_PATH)
            print("Modelo cargado correctamente")
            return True
        else:
            print(f"Modelo no encontrado en: {MODEL_PATH}")
            return False
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
        return False
def _open_camera():
    global camera
    if camera is not None and camera.isOpened():
        return True

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        return False

    camera = cap
    return True


def _release_camera():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()
    camera = None


def _warning_frame(message):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    ok, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes() if ok else b""


def _emit_danger_alert(objetos_peligrosos):
    socketio.emit('alerta_peligro', {
        'mensaje': 'OBJETO PELIGROSO DETECTADO',
        'objetos': objetos_peligrosos,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })


def generate_frames():
    global is_running
    # Mensajes solo ASCII: cv2.putText no dibuja bien tildes/UTF-8 en muchos sistemas.
    camera_error_frame = _warning_frame("Camara no disponible")
    waiting_frame = _warning_frame("Pulse INICIAR en esta pagina (Flask)")

    while True:
        with lock:
            current_running = is_running

        if not current_running:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   waiting_frame + b'\r\n')
            time.sleep(0.25)
            continue

        with lock:
            if not _open_camera():
                is_running = False
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       camera_error_frame + b'\r\n')
                time.sleep(0.5)
                continue

            success, frame = camera.read()

        if not success or frame is None:
            with lock:
                _release_camera()
            time.sleep(0.2)
            continue

        try:
            results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        except Exception as e:
            print(f"Error en detección: {e}")
            continue

        frame_has_danger = False
        objetos_peligrosos = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = result.names[cls_id]

                color = (0, 255, 0)

                if label.lower() in DANGEROUS_LABELS:
                    color = (0, 0, 255)
                    frame_has_danger = True
                    objetos_peligrosos.append({
                        'label': label,
                        'confidence': round(conf, 2),
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                cv2.putText(frame, f"{label} {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, color, 2)

                tracker.add_detection(label, conf)

        if frame_has_danger:
            _emit_danger_alert(objetos_peligrosos)
            cv2.putText(frame,
                        "ALERTA: OBJETO PELIGROSO",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame_bytes + b'\r\n')

# -----------------------------
# RUTAS
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start', methods=['POST'])
def start_camera():
    global is_running, camera

    if model is None:
        return jsonify({'success': False, 'message': 'Modelo no cargado'}), 400

    with lock:
        if is_running:
            return jsonify({'success': True, 'message': 'Camara ya estaba activa'})

        if not _open_camera():
            return jsonify({'success': False, 'message': 'No se pudo abrir la camara'}), 500

        is_running = True

    return jsonify({'success': True, 'message': 'Camara iniciada'})

@app.route('/api/stop', methods=['POST'])
def stop_camera():
    global is_running, camera

    try:
        with lock:
            is_running = False
            _release_camera()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(tracker.get_history())

@app.route('/api/detect', methods=['POST'])
def detect_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']

    if model is None:
        return jsonify({'error': 'Modelo no cargado'}), 503

    try:
        img_bytes = file.read()
        image = Image.open(BytesIO(img_bytes)).convert('RGB')
        frame = np.array(image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                conf = float(box.conf[0])
                label = result.names[int(box.cls[0])]

                tracker.add_detection(label, conf)

                detections.append({
                    'label': label,
                    'confidence': conf,
                    'box': [x1, y1, x2 - x1, y2 - y1]
                })

        dangerous_detections = [d for d in detections if d['label'].lower() in DANGEROUS_LABELS]
        if dangerous_detections:
            _emit_danger_alert([
                {
                    'label': d['label'],
                    'confidence': round(float(d['confidence']), 2),
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                for d in dangerous_detections
            ])

        return jsonify({'detections': detections})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    tracker.clear_history()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    history = tracker.get_history()

    guns = sum(1 for d in history if d['class'].lower() in ['gun', 'arma', 'pistola'])
    knives = sum(1 for d in history if d['class'].lower() in ['knife', 'cuchillo'])

    conf_list = [d['confidence'] for d in history]
    avg_conf = round(np.mean(conf_list), 2) if len(conf_list) > 0 else 0

    return jsonify({
        'total_detections': len(history),
        'guns': guns,
        'knives': knives,
        'average_confidence': avg_conf
    })

# -----------------------------
# SOCKET IO
# -----------------------------
@socketio.on('connect')
def handle_connect():
    print("Cliente conectado")
    emit('response', {'data': 'Conectado'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Cliente desconectado")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == '__main__':
    validate_python_version()
    if load_model():
        print("Servidor en http://localhost:5000")
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    else:
        print("No se pudo iniciar")