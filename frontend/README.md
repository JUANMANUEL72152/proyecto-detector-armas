# 🔫 Detector de Armas con IA

Sistema de detección de armas en tiempo real usando **YOLOv8** y visión artificial.  
Detecta pistolas y cuchillos tanto desde la cámara en vivo como desde imágenes subidas.

---

## 📁 Estructura del proyecto

```
proyecto-detector-armas/
├── backend/
│   ├── app.py              # Servidor Flask unificado (cámara en vivo + imágenes)
│   ├── requirements.txt    # Dependencias Python
│   ├── models/
│   │   └── best.pt         # Modelo YOLOv8 entrenado
│   ├── templates/
│   │   └── index.html      # Interfaz web clásica (Flask)
│   └── static/
│       └── style.css       # Estilos de la interfaz Flask
└── frontend/
    ├── src/
    │   ├── App.js
    │   └── WeaponDetection_WebUI.jsx  # Interfaz React
    └── package.json
```

---

## ⚙️ Requisitos previos

- Python recomendado: **3.10 o 3.11**
- Node.js 18 o superior
- Una cámara web (para detección en tiempo real)

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/JUANMANUEL72152/proyecto-detector-armas.git
cd proyecto-detector-armas
```

### 2. Configurar el backend (Flask)

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Actualizar pip e instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Compatibilidad con versiones nuevas de Python

Este proyecto funciona mejor con **Python 3.10/3.11**.  
Si una persona usa una versión mucho más nueva (por ejemplo 3.12 o 3.13), algunas librerías de visión artificial o IA pueden no tener ruedas binarias listas para su sistema y fallar en la instalación.

Si ocurre un error de dependencias:

1. Verificar versión:
   ```bash
   python --version
   ```
2. En Windows, instalar y usar Python 3.11 explícitamente:
   ```bash
   py -3.11 -m venv venv
   venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Si ya existe un entorno anterior, recrearlo limpio:
   ```bash
   # Windows
   rmdir /s /q venv
   py -3.11 -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

En resumen: si con Python muy nuevo falla, la solución más estable es usar **Python 3.11** para el entorno virtual del proyecto.

#### Variables de entorno (opcional pero recomendado)

Crea un archivo `.env` en la carpeta `backend/` con:

```
SECRET_KEY=una_clave_larga_y_secreta
CAMERA_INDEX=0
```

Si no lo creas, el servidor usará una clave por defecto solo apta para desarrollo.
Si tienes varias cámaras, ajusta `CAMERA_INDEX` (0, 1, 2...) hasta seleccionar la correcta.

#### Iniciar el servidor

```bash
python app.py
```

El servidor queda disponible en: **http://localhost:5000**

---

### 3. Configurar el frontend (React)

```bash
# Desde la raíz del proyecto
cd frontend

# Instalar dependencias
npm install

# Iniciar la app React
npm start
```

La app React queda disponible en: **http://localhost:3000**

> ⚠️ El frontend React se comunica con el backend en `http://127.0.0.1:5000`.  
> Asegúrate de que el backend esté corriendo antes de usar el frontend.

---

## 🖥️ Modos de uso

El proyecto ofrece dos interfaces:

### Interfaz Flask (clásica)
Accede a **http://localhost:5000** en tu navegador.  
- Detección en tiempo real desde la cámara web
- Panel de estadísticas y historial de detecciones
- Botones para iniciar/detener/limpiar

### Interfaz React
Accede a **http://localhost:3000** en tu navegador.  
- Activa la cámara, captura un frame y envíalo al modelo
- Visualiza los bounding boxes sobre la imagen capturada

---

## 🔌 Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Interfaz web Flask |
| `GET` | `/video_feed` | Stream de video con detecciones en vivo |
| `POST` | `/api/start` | Inicia la cámara |
| `POST` | `/api/stop` | Detiene la cámara |
| `POST` | `/api/detect` | Detecta armas en una imagen subida (usado por React) |
| `GET` | `/api/history` | Devuelve el historial de detecciones |
| `POST` | `/api/clear-history` | Limpia el historial |
| `GET` | `/api/stats` | Estadísticas: total, pistolas, cuchillos, confianza promedio |

### Ejemplo: llamar `/api/detect` con curl

```bash
curl -X POST http://localhost:5000/api/detect \
  -F "file=@/ruta/a/tu/imagen.jpg"
```

Respuesta esperada:
```json
{
  "detections": [
    {
      "label": "gun",
      "confidence": 0.87,
      "box": [120.0, 45.0, 200.0, 150.0]
    }
  ]
}
```

---

## 🧠 Modelo

El archivo `backend/models/best.pt` es un modelo YOLOv8 personalizado entrenado para detectar:
- **Pistolas / guns**
- **Cuchillos / knives**

Si deseas reemplazarlo por uno propio, entrena con [Ultralytics YOLOv8](https://docs.ultralytics.com/) y coloca el nuevo `best.pt` en la misma ruta.

---

## 🛠️ Tecnologías usadas

| Capa | Tecnología |
|------|-----------|
| Detección IA | YOLOv8 (Ultralytics) |
| Backend | Flask + Flask-SocketIO |
| Visión artificial | OpenCV, Pillow |
| Frontend moderno | React + Tailwind CSS |
| Frontend clásico | HTML + CSS vanilla |

---

## 📝 Notas de desarrollo

- Los archivos `__pycache__` y `.pyc` no deben subirse al repositorio. Están excluidos en `.gitignore`.
- En producción, configurar `SECRET_KEY` como variable de entorno y restringir `CORS` a los dominios específicos.
- El historial de detecciones se guarda en memoria RAM y se pierde al reiniciar el servidor.
- Si `pip install -r requirements.txt` muestra caracteres extraños (`F\x00l\x00a...`), el archivo `requirements.txt` tiene codificación incorrecta. Debe guardarse en **UTF-8**.
