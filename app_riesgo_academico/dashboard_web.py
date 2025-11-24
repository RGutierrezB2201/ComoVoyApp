import os
import json
from flask import Flask, render_template, abort, jsonify

app = Flask(__name__)

# Define la ruta absoluta al archivo JSON (usando app.root_path para robustez)
DATA_PATH = os.path.join(
    app.root_path,
    "static",
    "dashboard_data.json"
)


# Función auxiliar para cargar los datos del JSON
def load_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("estudiantes", [])
    except Exception as e:
        # En caso de error, retornar una lista vacía y registrar el error
        print(f"Error al cargar el archivo JSON: {e}")
        return []


# --- Rutas existentes ---

@app.route("/dashboard_data")
def dashboard_data():
    # Usamos jsonify aquí para devolver la data completa al cliente (aunque
    # en la versión final de la solución anterior usamos send_from_directory,
    # usar jsonify es más idiomático si no se quiere exponer la carpeta static)
    data = load_data()
    # Si quieres enviar el objeto completo con timestamp y alertas:
    # return jsonify({"estudiantes": data, "timestamp": "...", "alertas_count": len(data)})
    # Pero para mantener la compatibilidad con el front-end anterior,
    # usaremos la ruta de la versión robusta que busca en static
    from flask import send_from_directory
    STATIC_FOLDER = os.path.join(app.root_path, "static")
    return send_from_directory(STATIC_FOLDER, "dashboard_data.json")


@app.route("/")
def dashboard():
    return render_template("dashboard_docente.html")


# --- NUEVA VISTA DE DETALLE ---

@app.route("/detalle/<int:student_id>")
def detalle_estudiante(student_id):
    # 1. Cargar la lista de estudiantes
    estudiantes = load_data()

    # 2. Buscar al estudiante por ID
    student = next((item for item in estudiantes if item.get('id') == student_id), None)

    # 3. Manejar el caso de estudiante no encontrado
    if student is None:
        # Flask tiene una función abort para generar un error 404
        abort(404, description=f"Estudiante con ID {student_id} no encontrado.")

    # 4. Renderizar la nueva plantilla con los datos del estudiante
    return render_template("detalle_estudiante.html", student=student)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)