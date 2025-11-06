from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from io import BytesIO
from PIL import Image


from ultralytics import YOLO
model = YOLO("models/best.pt")

# Aquí se crea la app, esto es lo que Uvicorn busca
app = FastAPI()

# Permitir que el frontend (React) se comunique con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar tu modelo YOLOv8 entrenado
model = YOLO("models/best.pt")

@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}

@app.post("/api/detect")
async def detect_weapon(file: UploadFile = File(...)):
    # Leer imagen y convertir a formato PIL
    contents = await file.read()
    image = Image.open(BytesIO(contents)).convert("RGB")

    # Ejecutar la detección
    results = model(image)
    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf[0])
        label = model.names[int(box.cls[0])]
        detections.append({
            "label": label,
            "confidence": conf,
            "box": [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]
        })

    return {"detections": detections}
