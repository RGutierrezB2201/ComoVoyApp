# /app.py (En la carpeta raíz del proyecto)

import subprocess
import time
import os
import sys

# Definición de las rutas relativas de los scripts a ejecutar
PYTHON_BIN = sys.executable

API_SCRIPT = './api/app.py'  # Corregido de api_datos_universidad a api
AGENTE_SCRIPT = './app_riesgo_academico/agente_prediccion.py'
DASHBOARD_SCRIPT = './app_riesgo_academico/dashboard_web.py'

# Puertos y secuencia de comandos
PROCESOS = [
    {"name": "API de Datos (Puerto 5000)", "cmd": [PYTHON_BIN, API_SCRIPT], "delay": 5},
    {"name": "Agente de Predicción", "cmd": [PYTHON_BIN, AGENTE_SCRIPT], "delay": 5},
    {"name": "Dashboard Web (Puerto 5001)", "cmd": [PYTHON_BIN, DASHBOARD_SCRIPT], "delay": 2}
]


def iniciar_proyecto_completo():
    """
    Inicia la API, el Agente y el Dashboard en paralelo.
    """
    print("--- INICIANDO PROYECTO DE RIESGO ACADÉMICO ---")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    procesos_iniciados = []

    for p in PROCESOS:
        print(f"\n[INICIO] Ejecutando: {p['name']}...")

        try:
            proceso = subprocess.Popen(p['cmd'],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       cwd=os.getcwd())
            procesos_iniciados.append(proceso)
            print(f"[STATUS] '{p['name']}' iniciado con PID {proceso.pid}. Esperando {p['delay']}s...")

            time.sleep(p['delay'])

        except Exception as e:
            print(
                f"[ERROR] Error al iniciar {p['name']}. Revise si el script existe y las librerías están instaladas: {e}")
            detener_procesos(procesos_iniciados)
            sys.exit(1)

    dashboard_url = "http://127.0.0.1:5001/"
    print(f"\n[ABRIR] Abriendo Dashboard en: {dashboard_url}")

    try:
        import webbrowser
        webbrowser.open(dashboard_url)
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo abrir el navegador automáticamente. Visita: {dashboard_url}")

    print("\n--- PROYECTO INICIADO ---")
    print("Mantén esta terminal abierta. Presiona Ctrl+C para detener todos los procesos.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[DETECCIÓN] Señal de detención (Ctrl+C) recibida.")
        detener_procesos(procesos_iniciados)


def detener_procesos(procesos):
    """
    Detiene todos los procesos iniciados.
    """
    print("\n--- DETENIENDO PROCESOS ---")
    for p in procesos:
        if p.poll() is None:
            p.terminate()
            p.wait()
            print(f"[DETENIDO] Proceso con PID {p.pid} terminado.")

    print("--- PROYECTO APAGADO ---")


if __name__ == '__main__':
    try:
        import requests
        import pandas
        import joblib
        import flask
    except ImportError as e:
        print(f"\n[ERROR CRÍTICO] Falta una librería esencial: {e.name}. Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    iniciar_proyecto_completo()