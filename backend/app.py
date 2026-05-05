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

# Cargar variables de entorno desde .env
load_dotenv()

# -----------------------------
# CONFIGURACIÓN DE LA APP
# -----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta_segura')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Rutas y parámetros
MODEL_PATH = "models/best.pt"  # tu modelo entrenado
CONFIDENCE_THRESHOLD = 0.5
MAX_HISTORY = 50

# Variables globales
model = None
camera = None
is_running = False
lock = threading.Lock()

# Historial de detecciones
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

# -----------------------------
# CARGA DEL MODELO
# -----------------------------
def load_model():
    global model
    try:
        import torch
        from torch.serialization import add_safe_globals
        from ultralytics.nn.tasks import DetectionModel
        from torch.nn.modules.container import Sequential

        # Permitimos explícitamente las clases necesarias
        add_safe_globals([DetectionModel, Sequential])

        if os.path.exists(MODEL_PATH):
            print(f"Cargando modelo desde {MODEL_PATH} ...")
            # Forzamos weights_only=False para PyTorch >= 2.6
            model = YOLO(MODEL_PATH, task="detect")
            print(f"✅ Modelo cargado correctamente: {MODEL_PATH}")
            return True
        else:
            print(f"❌ Modelo no encontrado en: {MODEL_PATH}")
            return False

    except Exception as e:
        print(f"⚠ Error al cargar el modelo: {e}")
        return False

# -----------------------------
# FLUJO DE VIDEO Y DETECCIÓN
# -----------------------------
def generate_frames():
    global camera, is_running

    # Intentar abrir la cámara
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not camera.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        is_running = False
        return

    print("✅ Cámara iniciada correctamente.")

    while is_running:
        success, frame = camera.read()

        # Si la cámara falla, intentar reconectarla automáticamente
        if not success or frame is None:
            print("⚠ Cámara desconectada o sin señal, intentando reconectar...")
            camera.release()
            time.sleep(1)
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            continue

        # Realizar detección con YOLO
        try:
            results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        except Exception as e:
            print(f"❌ Error en la detección: {e}")
            continue

        frame_has_danger = False

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = result.names[cls_id]

                # Color según tipo de objeto
                color = (0, 255, 0)
                if label.lower() in ["gun", "knife", "arma", "pistola", "cuchillo"]:
                    color = (0, 0, 255)
                    frame_has_danger = True

                # Dibujar rectángulo y texto
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                cv2.putText(frame, f"{label} {conf:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                tracker.add_detection(label, conf)

        # Mostrar alerta si se detectó un objeto peligroso
        if frame_has_danger:
            cv2.putText(frame, "⚠ ALERTA: OBJETO PELIGROSO DETECTADO",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Convertir frame a formato JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("⚠ Error al codificar frame.")
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    # Liberar cámara al finalizar
    if camera is not None and camera.isOpened():
        camera.release()
        cv2.destroyAllWindows()
        print("✅ Cámara liberada correctamente al finalizar.")
    else:
        print("ℹ Cámara ya estaba liberada.")

# -----------------------------
# RUTAS FLASK
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
    if not model:
        return jsonify({'success': False, 'message': 'Modelo no cargado'}), 400

    if not is_running:
        if camera is not None and camera.isOpened():
            camera.release()
        camera = None
        is_running = True
        return jsonify({'success': True, 'message': 'Cámara iniciada'})
    return jsonify({'success': False, 'message': 'Cámara ya está activa'})



@app.route('/api/stop', methods=['POST'])
def stop_camera():
    global is_running, camera
    try:
        if camera is not None and camera.isOpened():
            camera.release()
            cv2.destroyAllWindows()
            print("✅ Cámara liberada correctamente")
        else:
            print("ℹ Cámara no estaba activa o ya fue liberada.")
        is_running = False
        camera = None
        return jsonify({'success': True, 'message': 'Cámara detenida correctamente'})
    except Exception as e:
        print(f"❌ Error al detener la cámara: {e}")
        return jsonify({'success': False, 'message': str(e)})



@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(tracker.get_history())

@app.route('/api/detect', methods=['POST'])
def detect_image():
    """
    Recibe una imagen estática (upload desde el frontend React)
    y devuelve las detecciones en formato JSON.
    Antes solo existía en main.py (FastAPI) — ahora unificado aquí.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    if not model:
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

        return jsonify({'detections': detections})

    except Exception as e:
        return jsonify({'error': f'Error procesando imagen: {str(e)}'}), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    tracker.clear_history()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    history = tracker.get_history()
    guns = sum(1 for d in history if d['class'].lower() in ['gun', 'arma', 'pistola'])
    knives = sum(1 for d in history if d['class'].lower() in ['knife', 'cuchillo'])
    avg_conf = round(np.mean([d['confidence'] for d in history]), 2) if history else 0

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
    print("🟢 Cliente conectado")
    emit('response', {'data': 'Conectado al detector'})

@socketio.on('disconnect')
def handle_disconnect():
    print("🔴 Cliente desconectado")

# -----------------------------
# INICIO DE LA APP
# -----------------------------
if __name__ == '__main__':
    if load_model():
        print("🚀 Iniciando servidor en http://localhost:5000")
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ No se pudo iniciar: modelo no encontrado.")
