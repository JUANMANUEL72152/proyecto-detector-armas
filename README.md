# Detector de Armas con IA

Proyecto de detección de armas con YOLOv8, backend Flask y frontend React opcional.

## Documentación del trabajo (PREDICTA CAMPUS)

- **[docs/PREDICTA_CAMPUS.tex](docs/PREDICTA_CAMPUS.tex)** — informe en LaTeX *PREDICTA CAMPUS*. Compílalo con tu editor favorito o con `pdflatex` si tienes una distribución TeX instalada.
- **[notebooks/Detector_de_Armas.ipynb](notebooks/Detector_de_Armas.ipynb)** — notebook de descarga de datos (Roboflow), limpieza del dataset y pipeline de entrenamiento/evaluación con YOLOv8.

Antes de ejecutar la celda que descarga desde Roboflow, define tu clave **sin subirla al repositorio**:

- **Windows (PowerShell):**

  ```powershell
  $env:ROBOFLOW_API_KEY="tu_clave_roboflow_aqui"
  ```

- **macOS / Linux:**

  ```bash
  export ROBOFLOW_API_KEY=tu_clave_roboflow_aqui
  ```

## Compatibilidad oficial

- Python para el backend: `3.10`, `3.11`, `3.12`
- Node.js solo si usarás React: `18.x` o `20.x`

Si usas Python `3.13+`, puede funcionar, pero no está garantizado por dependencias de visión artificial.

## Puertos: qué abre cada cosa

- **`http://localhost:5000`** — servidor Flask por defecto. Aquí tienes la interfaz web incluida (HTML) y la cámara en vivo con detección (`/video_feed`). **Es lo que usarás si solo ejecutas `python app.py`**.
- **`http://localhost:3000`** — solo si en otra terminal corres `npm start` dentro de la carpeta `frontend/`. Si no lanzas React, **no existe** ese puerto.

## Opción A: ejecutar todo en local

### 1) Clonar repositorio

```bash
git clone https://github.com/JUANMANUEL72152/proyecto-detector-armas.git
cd proyecto-detector-armas
```

### 2) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Opcional por variables de entorno (sin crear archivo `.env`):

- **`CAMERA_INDEX`**: índice de cámara `0`, `1`, `2`, etc. Ejemplo en PowerShell:  
  `$env:CAMERA_INDEX="1"; python app.py`

Abre **`http://localhost:5000`**, pulsa **Iniciar camara** y comprueba el video.

### 3) Frontend React (opcional)

Solo si quieres la UI de React aparte:

```bash
cd frontend
npm install
npm start
```

Ahí usarás **`http://localhost:3000`**. El backend debe seguir en el puerto 5000.

## Opción B: backend en Docker

```bash
docker build -t detector-armas-backend ./backend
docker run --rm -p 5000:5000 detector-armas-backend
```

Variables opcionales, por ejemplo cámara distinta:

```bash
docker run --rm -p 5000:5000 -e CAMERA_INDEX=1 detector-armas-backend
```

### Docker Compose

Opcional — otra camara (`0`, `1`, ...). En PowerShell:

```powershell
$env:CAMERA_INDEX="1"
docker compose up --build
```

```bash
docker compose up --build
```

```bash
docker compose down
```

Notas:

- Docker deja igual el backend en **`http://localhost:5000`**.
- La detección por imagen (`/api/detect`) funciona bien.
- La webcam en vivo desde dentro del contenedor puede requerir ajustes en el equipo anfitrión.

## Si falla la instalación por la versión de Python

```bash
python --version
```

En Windows conviene crear el entorno con 3.11:

```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Validación rápida

- Backend arriba en **`http://localhost:5000`**
- Clic en **Iniciar camara** en la página de Flask y comprobar el video en vivo
