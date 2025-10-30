# app/models/estudiante_model.py

import bcrypt
from app.db import Db

def obtener_todos_estudiantes():
    """
    Regresa lista de estudiantes (matricula, nombre, email)
    Solo para pruebas / debug.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT matricula, nombre, paterno, email
            FROM estudiante
            ORDER BY matricula
            LIMIT 10;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print("Error en obtener_todos_estudiantes:", e)
        return []

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def crear_estudiante(matricula, nombre, paterno, materno, email, telefono, password_plano, rol="alumno"):
    """
    Inserta un estudiante nuevo con contraseña hasheada.
    """
    conn = None
    cursor = None
    try:
        # hash bcrypt
        password_hash = bcrypt.hashpw(password_plano.encode('utf-8'), bcrypt.gensalt())
        password_hash = password_hash.decode('utf-8')

        conn = Db.get_connection()
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO estudiante
            (matricula, nombre, paterno, materno, email, telefono, contrasenia, rol)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        cursor.execute(insert_sql, (
            matricula,
            nombre,
            paterno,
            materno,
            email,
            telefono,
            password_hash,
            rol
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Error en crear_estudiante:", e)
        if conn is not None:
            conn.rollback()
        return False

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def obtener_por_matricula(matricula):
    """
    Trae todos los datos de un estudiante por matricula.
    Regresa dict o None.
    """
    conn = None
    cursor = None
    try:
        conn = Db.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT matricula, nombre, paterno, contrasenia, rol
            FROM estudiante
            WHERE matricula = %s
            LIMIT 1;
        """
        cursor.execute(query, (matricula,))
        row = cursor.fetchone()
        return row

    except Exception as e:
        print("Error en obtener_por_matricula:", e)
        return None

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def validar_login(matricula, password_plano):
    """
    Valida el login:
    - busca alumno por matricula
    - compara bcrypt
    - si ok -> regresa dict con {matricula, nombre, rol}
    - si no ok -> regresa None
    """
    usuario = obtener_por_matricula(matricula)
    if not usuario:
        return None

    hash_guardado = usuario["contrasenia"].encode("utf-8")
    ok = bcrypt.checkpw(password_plano.encode("utf-8"), hash_guardado)

    if not ok:
        return None

    # login válido:
    return {
        "matricula": usuario["matricula"],
        "nombre": usuario["nombre"],
        "paterno": usuario["paterno"],
        "rol": usuario["rol"]
    }
