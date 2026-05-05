# Detector de Armas con IA

Proyecto de deteccion de armas con YOLOv8, backend Flask y frontend React.

## Compatibilidad oficial

- Python compatible para ejecucion local del backend: `3.10`, `3.11`, `3.12`
- Node.js recomendado para frontend: `18.x` o `20.x`

Si alguien usa Python `3.13+`, puede funcionar, pero no se garantiza por dependencias de vision artificial.

## Opcion A: Ejecucion local (recomendada para usar camara)

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
```

Crear archivo `backend/.env`:

```env
SECRET_KEY=una_clave_larga
CAMERA_INDEX=0
```

Iniciar backend:

```bash
python app.py
```

### 3) Frontend (nueva terminal)

```bash
cd frontend
npm install
npm start
```

Abrir `http://localhost:3000`.

## Opcion B: Backend en Docker (portabilidad)

Ideal para evitar diferencias entre PCs en instalacion de dependencias.

```bash
docker build -t detector-armas-backend ./backend
docker run --rm -p 5000:5000 --env-file ./backend/.env detector-armas-backend
```

### Opcion B1: Docker Compose (mas simple)

Con `docker-compose.yml` puedes levantar el backend con un solo comando:

```bash
docker compose up --build
```

Para detener:

```bash
docker compose down
```

Notas:
- Esta opcion estandariza dependencias del backend.
- La deteccion por imagen (`/api/detect`) funciona bien.
- El acceso directo a webcam desde contenedor puede requerir configuracion adicional del host/driver, por lo que para uso de camara en vivo suele ser mejor la Opcion A.

## Que hacer si falla por version de Python

1. Verificar version:
   ```bash
   python --version
   ```
2. Crear entorno con Python 3.11:
   ```bash
   py -3.11 -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Validacion rapida

- Backend arriba en `http://localhost:5000`
- Frontend arriba en `http://localhost:3000`
- En frontend: click en **Iniciar Camara**
- Aceptar permisos del navegador
- Verificar video y detecciones
