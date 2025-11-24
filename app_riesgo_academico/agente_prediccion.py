import json

import requests
import pandas as pd
import joblib
import time
from datetime import datetime
import os
import numpy as np


# Configuración general
API_URL = "http://127.0.0.1:5000/"
ENDPOINT_ESTUDIANTES = "/estudiantes"
MODELO_PATH = 'modelo/comovoy.joblib'
LOGS_CORREOS_PATH = 'logs/log_correos_simulados.txt'
CORREO_DESTINATARIO = 'docente@comovoy.cl'

#UMBRAL_RIESGO_ALTO = 0.60
#ALERTA_THRESHOLD = 0.50

REPORTE_DASHBOARD_PATH = 'static/dashboard_data.json'

def obtener_datos_de_api(url_base, endpoint):
    """
    Realiza una petición GET a la API para obtener una lista de estudiantes.
    """
    url_completa = url_base + endpoint
    print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Conectando a la API {url_completa}")
    try:
        response = requests.get(url_completa)
        response.raise_for_status()

        datos_json = response.json()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Datos recibidos correctamente desde la API. Total de estudiantes: {len(datos_json)}")
        return datos_json
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: No se pudo conectar a la API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR al obtener los datos de la API: {e}")
        return None


def cargar_modelo(path):
    """
    Carga el pipeline de predicción de riesgo guardado.
    :return:
    """
    if not os.path.exists(path):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: Modelo no encontrado")
        return None

    try:
        modelo = joblib.load(path)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Modelo ComoVoy cargado: {modelo}")
        return modelo
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR al cargar modelo: {e}")
        return None

def calcular_indice_riesgo(df, modelo, umbral_riesgo: float = 0.75):
    """
    Procesa los datos, realiza predicciones (probabilidad de reprobación) y calcula el indice de riesgo para cada estudiante.    :return:
    """
    if df.empty or modelo is None:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Error: No hay datos o modelo disponibles para calcular el riesgo.")
        return pd.DataFrame()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Realizando predicciones y calculando indice de riesgo")

    try:
        columnas_esperadas = list(modelo.feature_names_in_)

        # Mantener copia original para no perder el ID
        df_original = df.copy()

        # Detectar columnas faltantes
        faltantes = set(columnas_esperadas) - set(df.columns)
        if faltantes:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Columnas faltantes detectadas y agregadas: {faltantes}")

        for col in columnas_esperadas:
            if col not in df.columns:
                df_original[col] = "Desconocido"


        df_features = df_original[columnas_esperadas]

        # Predicción
        probabilidades = modelo.predict_proba(df_features)

        # Añadir columnas de riesgo a DF original
        df_original.loc[:, 'Riesgo_Probabilidad'] = probabilidades[:, 0]
        df_original.loc[:, 'Indice_Riesgo'] = (df_original['Riesgo_Probabilidad'] * 100).round().astype(int)
        df_original.loc[:, 'Nivel_Alerta'] = df_original['Riesgo_Probabilidad'].apply(
            lambda p: 'ALTO' if p >= umbral_riesgo else ('MEDIO' if p >= 0.40 else 'BAJO')
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cálculo de IR finalizado.")
        return df_original

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error durante la predicción de riesgo: {e}")
        return pd.DataFrame()


def generar_alertas_reportes(df_riesgo):
    """
    Genera mensajes de alerta, genera un reporte en csv y prepara los datos JSON para el dashboard HTML del docente
    :param df_riesgo:
    :return:
    """
    umbral_alerta = 0.75
    if df_riesgo.empty:
        return
    df_alertas = df_riesgo[df_riesgo['Riesgo_Probabilidad'] >= umbral_alerta].sort_values(
        by='Indice_Riesgo', ascending=False
    )

    if not df_alertas.empty:
        print("\n*** ALERTA DE RIESGO ACADÉMICO DETECTADA ***")
        for index, estudiante in df_alertas.iterrows():
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Estudiante ID {estudiante['id']} ({estudiante['Carrera']}):")
            print(f"  -> Nivel: {estudiante['Nivel_Alerta']} (IR: {estudiante['Indice_Riesgo']}%)")
        log_notificacion_riesgo(CORREO_DESTINATARIO, df_alertas)
    else:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] No se detectaron estudiantes que superen el umbral de ALERTA ({umbral_alerta * 100:.0f}%) en este ciclo.")

    df_carrera_riesgo = df_riesgo.groupby('Carrera').agg(
        Riesgo_Acumulado=('Indice_Riesgo', 'mean'),
        Total_Estudiantes=('id', 'count')
    ).reset_index()

    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'alertas_count': len(df_alertas),
        'riesgo_por_carrera': df_carrera_riesgo.to_dict('records'),
        'estudiantes': df_riesgo.to_dict('records')
    }

    try:
        with open(REPORTE_DASHBOARD_PATH, 'w') as f:
            json.dump(dashboard_data, f, indent=4)
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Datos de Dashboard JSON generados: '{REPORTE_DASHBOARD_PATH}'")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR al guardar el JSON del dashboard: {e}")

def monitorear_datos_institucionales():
    """
    Monitorea continuamente el riesgo de reprobación de los estudiantes.
    Carga el modelo, obtiene datos, realiza la predicción y genera reportes.
    :return:
    """
    modelo_riesgo = cargar_modelo(MODELO_PATH)
    if modelo_riesgo is None:
        return

    while True:
        print("\n" + "=" * 80)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INICIO DEL CICLO DE MONITOREO DE RIESGO ACADÉMICO")
        print("\n" + "=" * 80)

        datos_raw = obtener_datos_de_api(API_URL, ENDPOINT_ESTUDIANTES)
        if datos_raw:
            df_datos = pd.DataFrame(datos_raw)
            df_riesgo = calcular_indice_riesgo(df_datos, modelo_riesgo)
            if not df_riesgo.empty:
                generar_alertas_reportes(df_riesgo)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Esperando 60 segundos para el siguiente ciclo...")
        time.sleep(60)

def log_notificacion_riesgo(destinatario, estudiantes_en_riesgo):
    """
    Simula el envío de un correo y registra la alerta en un archivo de log
    :param destinatario:
    :param estudiantes_en_riesgo:
    :return:
    """

    fecha_log = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    asunto = f"ALERTA SIMULADA: Estudiantes en Riesgo Académico, {len(estudiantes_en_riesgo)}: {fecha_log}"

    log_content = [
        "=" * 50,
        f"FECHA/HORA: {fecha_log}",
        f"DESTINATARIO: {destinatario}",
        f"ASUNTO: {asunto}",
        f"ESTUDIANTES EN ALERTA ({len(estudiantes_en_riesgo)}):"
    ]

    for index, estudiante in estudiantes_en_riesgo.iterrows():
        log_content.append(
            f"  - ID: {estudiante['id']}, Carrera: {estudiante['Carrera']}, Nivel: {estudiante['Nivel_Alerta']}, IR: {estudiante['Indice_Riesgo']}%"
        )
    log_content.append("=" * 50 + "\n")

    log_message = "\n".join(log_content)

    try:
        with open(LOGS_CORREOS_PATH, 'a') as f:
            f.write(log_message)

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] LOG: Correo de alerta simulado guardado en '{LOGS_CORREOS_PATH}'. Casos: {len(estudiantes_en_riesgo)}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR al escribir el log de correo simulado: {e}")

if __name__ == "__main__":
    monitorear_datos_institucionales()