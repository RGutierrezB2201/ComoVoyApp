from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

# Configuración de la API
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'comovoy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Estudiante(db.Model):
    """
    Modelo de SQLAlchemy que define la estructura de la tabla estudiantes con todos los campos que lo definen.
    """

    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)

    Aprobado = db.Column(db.Integer)  # 0 = Reprobado, 1 = Aprobado
    Nota_final = db.Column(db.Integer)
    C1 = db.Column(db.Integer)
    C2 = db.Column(db.Integer)
    CR = db.Column(db.Integer)
    Prom_certamenes = db.Column(db.Integer)
    Prom_cuestionarios = db.Column(db.Integer)
    T_U1_U2 = db.Column(db.Integer)
    T_U3_U5 = db.Column(db.Integer)
    T_Listas = db.Column(db.Integer)
    T_Texto_Archivos = db.Column(db.Integer)
    Prom_tareas = db.Column(db.Integer)
    Ctrl_U1 = db.Column(db.Integer)
    Ctrl_U2 = db.Column(db.Integer)
    Ctrl_U3_Ciclos = db.Column(db.Integer)
    Ctrl_U5_Func = db.Column(db.Integer)
    Ctrl_U6_Strings = db.Column(db.Integer)
    Ctrl_U7 = db.Column(db.Integer)
    Ctrl_Diccionarios = db.Column(db.Integer)
    Ctrl_U10 = db.Column(db.Integer)
    Prom_controles = db.Column(db.Integer)
    TS_U1 = db.Column(db.Integer)
    TS_U2 = db.Column(db.Integer)
    TS_U3 = db.Column(db.Integer)
    TS_U5 = db.Column(db.Integer)
    TS_U6 = db.Column(db.Integer)
    TS_U7 = db.Column(db.Integer)
    TS_U8 = db.Column(db.Integer)
    Prom_tickets_salida = db.Column(db.Integer)
    C1_R = db.Column(db.Integer)
    C2_R = db.Column(db.Integer)

    # Campos Categóricos/Demográficos (object)
    Genero = db.Column(db.String(10))
    Region = db.Column(db.String(50))
    Carrera = db.Column(db.String(100))
    Jornada = db.Column(db.String(20))
    Via_Ingreso = db.Column(db.String(50))
    Rama_Educacional = db.Column(db.String(50))
    Dependencia = db.Column(db.String(50))

    # Campos de Admisión/Otros (float64)
    NEM = db.Column(db.Float)
    Ano_Egreso = db.Column(db.Float)
    Puntaje_Ponderado = db.Column(db.Float)
    Puntaje_NEM = db.Column(db.Float)
    Puntaje_Ranking = db.Column(db.Float)
    Puntaje_Lenguaje = db.Column(db.Float)
    Puntaje_Mat_M1 = db.Column(db.Float)
    Puntaje_Mat_M2 = db.Column(db.Float)
    Puntaje_Historia = db.Column(db.Float)
    Puntaje_Ciencias = db.Column(db.Float)
    Nota_Test_Ingreso = db.Column(db.Float)
    LAWSON_PRE = db.Column(db.Float)

    def to_dict(self):
        """
        Serialización del objeto Estudiante a un diccionario.
        :return:
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Rutas de la API
@app.route('/estudiantes', methods=['GET'])
def get_estudiantes():
    """
    Ruta para obtener la lista completa de estudiantes.
    """
    estudiantes = Estudiante.query.all()
    return jsonify([e.to_dict() for e in estudiantes])


@app.route('/estudiante/<int:estudiante_id>', methods=['GET'])
def get_estudiante(estudiante_id):
    """
    Ruta para obtener los datos de un estudiante por su ID
    """
    estudiante = Estudiante.query.get(estudiante_id)
    if estudiante is None:
        return jsonify({'error': 'Estudiante no encontrado'}), 404
    return jsonify({'estudiante': estudiante.to_dict()})


@app.route('/estudiante/<int:estudiante_id>', methods=['PUT'])
def actualizar_estudiante(estudiante_id):
    """
    Ruta para actualizar los datos de un estudiante existente (PUT)
    :param estudiante_id:
    :return:
    """
    estudiante = Estudiante.query.get(estudiante_id)

    if estudiante is None:
        return jsonify({'error': 'Estudiante no encontrado'}), 404

    datos_actualizacion = request.get_json()
    if not datos_actualizacion:
        return jsonify({'error': 'No se entregaron datos para actualizar'}), 404

    for campo, valor in datos_actualizacion.items():
        if hasattr(estudiante, campo):
            setattr(estudiante, campo, valor)
        else:
            return jsonify({'error': f'campo "{campo}" no válido para el estudiante'}), 404
    try:
        db.session.commit()
        return jsonify({
            'mensaje': f'Datos actualizados correctamente para el estudiante {estudiante_id}',
            'datos_actualizados': estudiante.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return  jsonify({'error': f'Error al guardar en la base de datos: {e}'}), 500
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)