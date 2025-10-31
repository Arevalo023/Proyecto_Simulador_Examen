# app/models/exam_model.py

from app.db import Db
import random
import time

def contar_intentos(matricula, tipo_test):
    """
    Cuenta cuántos intentos tiene este alumno de un tipo ('practica' o 'final').
    Sirve para checar el limite (6 practica, 3 final)
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT COUNT(*) 
            FROM intentos_examen
            WHERE matricula = %s
              AND tipo_test = %s;
        """
        cursor.execute(sql, (matricula, tipo_test))
        row = cursor.fetchone()
        if row:
            return row[0]
        return 0
    except Exception as e:
        print("Error en contar_intentos:", e)
        return 0
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def crear_intento(matricula, tipo_test):
    """
    Crea un intento_examen en 0 puntos todavía.
    Regresa id_intento (PK autoincrement) o None si falla.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO intentos_examen
                (matricula, tipo_test, calificacion, aprobado, duracion_segundos_total)
            VALUES
                (%s, %s, 0.00, 0, NULL);
        """
        cursor.execute(sql, (matricula, tipo_test))
        conn.commit()

        return cursor.lastrowid

    except Exception as e:
        print("Error en crear_intento:", e)
        if conn: conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def seleccionar_preguntas_aleatorias(limit_preguntas):
    """
    Devuelve una lista de dict con id_pregunta, reactivo, codigo_imagen.
    RAND() en SQL nos da aleatorio.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = f"""
            SELECT p.id_pregunta,
                   p.reactivo,
                   p.codigo_imagen
            FROM preguntas p
            ORDER BY RAND()
            LIMIT {limit_preguntas};
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print("Error en seleccionar_preguntas_aleatorias:", e)
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def registrar_preguntas_en_intento(id_intento, lista_preguntas):
    """
    Mete cada pregunta en examen_respuestas con (id_intento, id_pregunta)
    aún sin respuesta. Regresa True/False.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO examen_respuestas
                (id_intento, id_pregunta, contestada_a_tiempo)
            VALUES
                (%s, %s, 1);
        """

        for preg in lista_preguntas:
            cursor.execute(sql, (id_intento, preg["id_pregunta"]))

        conn.commit()
        return True

    except Exception as e:
        print("Error en registrar_preguntas_en_intento:", e)
        if conn: conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def obtener_estado_pregunta(id_intento, indice):
    """
    Regresa la pregunta #indice (0-based) del intento, con las opciones mezcladas.
    También regresa total para que sepamos cuántas son.
    """
    conn = None
    cursor = None

    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        sql_pregs = """
            SELECT 
                er.id_seleccion,
                er.id_pregunta,
                p.reactivo,
                p.codigo_imagen,
                bi.ruta AS imagen_ruta
            FROM examen_respuestas er
            INNER JOIN preguntas p 
                ON p.id_pregunta = er.id_pregunta
            LEFT JOIN banco_imagenes bi
                ON bi.codigo_imagen = p.codigo_imagen
            WHERE er.id_intento = %s
            ORDER BY er.id_seleccion ASC;
        """
        cursor.execute(sql_pregs, (id_intento,))
        todas = cursor.fetchall()

        total = len(todas)
        if indice < 0 or indice >= total:
            return None

        actual = todas[indice]
        id_pregunta = actual["id_pregunta"]

        sql_resp = """
            SELECT r.id_respuesta,
                   r.opcion,
                   r.ok
            FROM respuestas r
            WHERE r.id_pregunta = %s;
        """
        cursor.execute(sql_resp, (id_pregunta,))
        opciones = cursor.fetchall()

        random.shuffle(opciones)

        return {
            "total": total,
            "index": indice,
            "pregunta": {
                "id_pregunta": id_pregunta,
                "texto": actual["reactivo"],
                "imagen_ruta": actual["imagen_ruta"]
            },
            "opciones": opciones
        }

    except Exception as e:
        print("Error en obtener_estado_pregunta:", e)
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def guardar_respuesta_de_pregunta(id_intento, id_pregunta, id_respuesta_elegida, contesto_a_tiempo, tiempo_seg):
    """
    Actualiza la fila en examen_respuestas con la opcion elegida.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE examen_respuestas
            SET id_respuesta_elegida = %s,
                contestada_a_tiempo = %s,
                tiempo_respuesta_segundos = %s
            WHERE id_intento = %s
              AND id_pregunta = %s;
        """
        cursor.execute(sql, (
            id_respuesta_elegida,
            1 if contesto_a_tiempo else 0,
            tiempo_seg,
            id_intento,
            id_pregunta
        ))
        conn.commit()
        return True

    except Exception as e:
        print("Error en guardar_respuesta_de_pregunta:", e)
        if conn: conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def calcular_calificacion_y_cerrar_intento(id_intento, tipo_test):
    """
    Calcula el % final:
    - practica: cada correcta vale 5 pts, 20 preguntas => 100
    - final: cada correcta vale 2.5 pts, 40 preguntas => 100
    Luego guarda calificacion y aprobado en intentos_examen.
    Regresa dict con calificacion y aprobado.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. obtener todas las respuestas elegidas en este intento
        sql = """
            SELECT er.id_pregunta,
                   er.id_respuesta_elegida,
                   er.contestada_a_tiempo,
                   r.ok
            FROM examen_respuestas er
            LEFT JOIN respuestas r
                ON r.id_respuesta = er.id_respuesta_elegida
            WHERE er.id_intento = %s;
        """
        cursor.execute(sql, (id_intento,))
        rows = cursor.fetchall()

        correctas = 0
        total = len(rows)

        for row in rows:
            # correcta si (eligio algo) && (ok=1) && (contestada a tiempo)
            if row["id_respuesta_elegida"] is not None and row["ok"] == 1 and row["contestada_a_tiempo"] == 1:
                correctas += 1

        # 2. ponderar según tipo_test
        if tipo_test == "practica":
            puntos = correctas * 5.0
        else:
            # final
            puntos = correctas * 2.5

        calificacion = puntos  # ya 0-100
        aprobado = 1 if calificacion >= 75.0 else 0

        # 3. actualizar intento
        cursor2 = conn.cursor()
        sql_upd = """
            UPDATE intentos_examen
            SET calificacion = %s,
                aprobado = %s
            WHERE id_intento = %s;
        """
        cursor2.execute(sql_upd, (calificacion, aprobado, id_intento))
        conn.commit()
        cursor2.close()

        return {
            "total_preguntas": total,
            "correctas": correctas,
            "calificacion": calificacion,
            "aprobado": aprobado
        }

    except Exception as e:
        print("Error en calcular_calificacion_y_cerrar_intento:", e)
        if conn: conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def obtener_historial_intentos(matricula, tipo_test):
    """
    Regresa lista de intentos de un alumno para un tipo de test ('practica' o 'final').
    Cada intento incluye fecha, calificacion, aprobado.
    Ordenado más reciente primero.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT 
                id_intento,
                fecha_hora_realiza,
                calificacion,
                aprobado
            FROM intentos_examen
            WHERE matricula = %s
              AND tipo_test = %s
            ORDER BY fecha_hora_realiza DESC;
        """
        cursor.execute(sql, (matricula, tipo_test))
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print("Error en obtener_historial_intentos:", e)
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
