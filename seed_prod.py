# seed_prod.py
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'user': 'root',
    'password': '',
    #'password' = "Carro2020!",
    'host': 'localhost',
    'database': 'simulador_manejo',
    'port': 3306
}

# --- GENERAR LISTA DE ESTUDIANTES ---
ESTUDIANTES_A_CREAR = []

# 1 ADMINISTRADOR
ESTUDIANTES_A_CREAR.append({
    'matricula': 1,
    'nombre': 'Admin',
    'paterno': 'Principal',
    'materno': None,
    'email': 'admin@simulador.com',
    'telefono': 8111111111,
    'password_plano': 'AdminSeguro123!',
    'rol': 'admin'
})

# 25 ALUMNOS
for i in range(1, 26):
    ESTUDIANTES_A_CREAR.append({
        'matricula': i + 1,  # evita conflicto con admin
        'nombre': f'Alumno{i}',
        'paterno': 'Ejemplo',
        'materno': None,
        'email': f'alumno{i:02d}@simulador.com',
        'telefono': 5500000000 + i,  # genera un teléfono distinto
        'password_plano': f'pass_alumno_{i:02d}!',
        'rol': 'alumno'
    })

def poblar_estudiantes():
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        print("Conectado a la base de datos de producción.")

        for est in ESTUDIANTES_A_CREAR:
            hashed_password = generate_password_hash(
                est['password_plano'],
                method='pbkdf2:sha256'
            )

            sql = """
                INSERT INTO estudiante
                (matricula, nombre, paterno, materno, email, telefono, contrasenia, rol)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                est['matricula'],
                est['nombre'],
                est['paterno'],
                est['materno'],
                est['email'],
                est['telefono'],
                hashed_password,
                est['rol']
            )

            try:
                cursor.execute(sql, val)
                print(f"Usuario '{est['email']}' ({est['rol']}) creado exitosamente.")
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    print(f"Advertencia: El email o matrícula '{est['email']}' ya existe. Omitiendo.")
                else:
                    print(f"Error al insertar '{est['email']}': {err}")

        db.commit()
        print("\n✅ ¡Población de estudiantes completada!")

    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()
            print("Conexión cerrada.")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    print("=========================================================")
    print("  SCRIPT DE POBLACIÓN DE TABLA 'estudiante' (PRODUCCIÓN) ")
    print("=========================================================")
    print(f"Base de datos objetivo: {DB_CONFIG['database']} en {DB_CONFIG['host']}")

    confirmacion = input("¿Estás SEGURO de que quieres insertar estos estudiantes? (escribe 'si' para confirmar): ")
    if confirmacion.lower() == 'si':
        poblar_estudiantes()
    else:
        print("Operación cancelada.")