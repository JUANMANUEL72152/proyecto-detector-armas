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
