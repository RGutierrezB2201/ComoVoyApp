from app import app, db, Estudiante
from faker import Faker
import random
import numpy as np

fake = Faker('es_CL')
NUM_REGISTROS = 100
PROB_BAJO_RENDIMIENTO = 0.40

GENEROS = ['Femenino', 'Masculino']
REGIONES = [fake.city() for _ in range(16)]
CARRERAS = ['Ingeniería Civil Informática', 'Ingeniería Civil Industrial', 'Ingeniería Ejecución en Computación e Informática']
JORNADAS = ['Diurna', 'Vespertina']
VIAS_INGRESO = ['PSU_PTU', 'PACE', 'Talento Deportivo', 'Traslado']
RAMAS_EDUCACIONALES = ['Científico Humanísta', 'Técnico Profesional']
DEPENDENCIAS = ['Municipal', 'Particular Subvencionado', 'Particular Pagado']

def generar_notas(es_bajo_rendimiento):
    """
    Genera una nota entera con sesgo:
    - Bajo rendimiento: notas entre 1 y 100 concentradas en el rango de reprobación (1-54)
    - Alto rendimiento: notas entre 55 y 100
    :param es_bajo_rendimiento:
    :return:
    """

    if es_bajo_rendimiento:
        return random.triangular(1, 100, 40)
    else:
        return random.triangular(60, 100, 80)


def generar_float_rango(min_val, max_val, decimales=2):
    """
    Genera un numero decimal en el rango dado
    """
    return round(random.uniform(min_val, max_val), decimales)

def generar_datos_estudiante(es_bajo_rendimiento):
    """
    Crea una instancia de estudiante con datos simulados y sesgo hacia la reprobación
    """
    nota_final = int(generar_notas(es_bajo_rendimiento))
    aprobado = 1 if nota_final >= 55 else 0

    nem_base = generar_float_rango(1.0, 5.0, 1) if es_bajo_rendimiento else generar_float_rango(5.5, 7.0, 1)
    puntaje_base = random.randint(300, 600) if es_bajo_rendimiento else random.randint(650, 950)

    return Estudiante(
        Aprobado=aprobado,
        Nota_final=nota_final,
        C1=int(generar_notas(es_bajo_rendimiento)),
        C2=int(generar_notas(es_bajo_rendimiento)),
        CR=int(generar_notas(es_bajo_rendimiento)),
        Prom_certamenes=int(generar_notas(es_bajo_rendimiento)),
        Prom_cuestionarios=int(generar_notas(es_bajo_rendimiento)),
        T_U1_U2=int(generar_notas(es_bajo_rendimiento)),
        T_U3_U5=int(generar_notas(es_bajo_rendimiento)),
        T_Listas=int(generar_notas(es_bajo_rendimiento)),
        T_Texto_Archivos=int(generar_notas(es_bajo_rendimiento)),
        Prom_tareas=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U1=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U2=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U3_Ciclos=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U5_Func=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U6_Strings=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U7=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_Diccionarios=int(generar_notas(es_bajo_rendimiento)),
        Ctrl_U10=int(generar_notas(es_bajo_rendimiento)),
        Prom_controles=int(generar_notas(es_bajo_rendimiento)),
        TS_U1=int(generar_notas(es_bajo_rendimiento)),
        TS_U2=int(generar_notas(es_bajo_rendimiento)),
        TS_U3=int(generar_notas(es_bajo_rendimiento)),
        TS_U5=int(generar_notas(es_bajo_rendimiento)),
        TS_U6=int(generar_notas(es_bajo_rendimiento)),
        TS_U7=int(generar_notas(es_bajo_rendimiento)),
        TS_U8=int(generar_notas(es_bajo_rendimiento)),
        Prom_tickets_salida=int(generar_notas(es_bajo_rendimiento)),
        C1_R=int(generar_notas(es_bajo_rendimiento)),
        C2_R=int(generar_notas(es_bajo_rendimiento)),
        Genero=random.choice(GENEROS),
        Region=random.choice(REGIONES),
        Carrera=random.choice(CARRERAS),
        Jornada=random.choice(JORNADAS),
        Via_Ingreso=random.choice(VIAS_INGRESO),
        Rama_Educacional=random.choice(RAMAS_EDUCACIONALES),
        Dependencia=random.choice(DEPENDENCIAS),
        NEM=nem_base,
        Ano_Egreso=float(random.randint(2015, 2024)),
        Puntaje_Ponderado=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_NEM=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_Ranking=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_Lenguaje=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_Mat_M1=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_Mat_M2=generar_float_rango(puntaje_base, puntaje_base + 100) if random.random() > 0.3 else 100.0,
        Puntaje_Historia=generar_float_rango(puntaje_base, puntaje_base + 100),
        Puntaje_Ciencias=generar_float_rango(puntaje_base, puntaje_base + 100),
        Nota_Test_Ingreso=generar_float_rango(puntaje_base, puntaje_base + 100),
        LAWSON_PRE=generar_float_rango(1.0, 100.0)
    )

def poblar_db():
    """
    Borra y recrea la base de datos con datos simulados y sesgados.
    :return:
    """

    with app.app_context():
        db.drop_all()
        db.create_all()

        estudiantes = []
        for _ in range(NUM_REGISTROS):
            es_bajo_rendimiento = random.random() < PROB_BAJO_RENDIMIENTO
            estudiantes.append(generar_datos_estudiante(es_bajo_rendimiento))

        db.session.add_all(estudiantes)
        db.session.commit()
if __name__ == '__main__':
    poblar_db()