import mysql.connector
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    'user': 'root',
    'password': '',
    #'password' = "Carro2020!",
    'host': 'localhost',
    'database': 'simulador_manejo',
    'port': 3306
}

# ======================================================
# 1. Conexión
# ======================================================
def conectar():
    return mysql.connector.connect(**DB_CONFIG)

# ======================================================
# 2. Obtener alumnos, preguntas y respuestas
# ======================================================
def obtener_datos(cursor):
    cursor.execute("SELECT matricula FROM estudiante WHERE rol='alumno'")
    alumnos = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id_pregunta FROM preguntas")
    preguntas = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id_respuesta, id_pregunta, ok FROM respuestas")
    respuestas = cursor.fetchall()

    respuestas_por_pregunta = {}
    for id_respuesta, id_pregunta, ok in respuestas:
        respuestas_por_pregunta.setdefault(id_pregunta, []).append((id_respuesta, ok))

    return alumnos, preguntas, respuestas_por_pregunta

# ======================================================
# 3. Crear intentos y respuestas
# ======================================================
def poblar_intentos_y_respuestas():
    db = conectar()
    cursor = db.cursor()
    print("Conectado a la base de datos para poblar intentos y respuestas...")

    alumnos, preguntas, respuestas_por_pregunta = obtener_datos(cursor)

    if not preguntas:
        print("❌ No hay preguntas en la base de datos. No se pueden generar intentos.")
        return

    for matricula in alumnos:
        for tipo_test, num_preguntas in [("practica", 20), ("final", 40)]:
            preguntas_seleccionadas = random.sample(preguntas, min(num_preguntas, len(preguntas)))

            correctas = 0
            respuestas_a_insertar = []

            for id_pregunta in preguntas_seleccionadas:
                opciones = respuestas_por_pregunta.get(id_pregunta, [])
                if not opciones:
                    continue

                id_respuesta_elegida, ok = random.choice(opciones)
                if ok == 1:
                    correctas += 1

                respuestas_a_insertar.append({
                    'id_pregunta': id_pregunta,
                    'id_respuesta_elegida': id_respuesta_elegida,
                    'contestada_a_tiempo': random.choice([0, 1]),
                    'tiempo_respuesta_segundos': random.randint(10, 80)
                })

            total = len(respuestas_a_insertar)
            calificacion = (correctas / total) * 100 if total > 0 else 0
            aprobado = 1 if calificacion >= 75 else 0

            # Insertar intento
            sql_intento = """
                INSERT INTO intentos_examen
                (matricula, tipo_test, fecha_hora_realiza, calificacion, aprobado, duracion_segundos_total)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            fecha = datetime.now() - timedelta(days=random.randint(0, 10))
            duracion = sum([r['tiempo_respuesta_segundos'] for r in respuestas_a_insertar])
            val_intento = (matricula, tipo_test, fecha, calificacion, aprobado, duracion)
            cursor.execute(sql_intento, val_intento)
            id_intento = cursor.lastrowid

            # Insertar respuestas asociadas
            sql_resp = """
                INSERT INTO examen_respuestas
                (id_intento, id_pregunta, id_respuesta_elegida, contestada_a_tiempo, tiempo_respuesta_segundos)
                VALUES (%s, %s, %s, %s, %s)
            """
            for r in respuestas_a_insertar:
                val_resp = (id_intento, r['id_pregunta'], r['id_respuesta_elegida'],
                            r['contestada_a_tiempo'], r['tiempo_respuesta_segundos'])
                cursor.execute(sql_resp, val_resp)

            print(f"Alumno {matricula} → Intento '{tipo_test}' con {total} preguntas → "
                  f"{calificacion:.2f}% ({'aprobado' if aprobado else 'reprobado'})")

    db.commit()
    print("\n✅ ¡Población de intentos y respuestas completada con éxito!")
    cursor.close()
    db.close()

# ======================================================
# EJECUCIÓN
# ======================================================
if __name__ == "__main__":
    print("=========================================================")
    print("   SCRIPT DE POBLACIÓN DE INTENTOS Y RESPUESTAS EXAMEN   ")
    print("=========================================================")
    confirmacion = input("¿Deseas poblar intentos y respuestas simuladas? (escribe 'si' para confirmar): ")

    if confirmacion.lower() == 'si':
        poblar_intentos_y_respuestas()
    else:
        print("Operación cancelada.")
