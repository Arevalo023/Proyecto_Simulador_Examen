# app/models/dashboard_model.py

from app.db import Db 
from decimal import Decimal

class DashboardModel:

    # --- QUERIES PARA ALUMNO ---

    @staticmethod
    def get_temas_fallidos_alumno(matricula):
        """
        Obtiene los temas (categorías) donde más se equivoca un alumno.
        """
        conn = None # Inicializamos
        try:
            conn = Db.get_connection() 
            cursor = conn.cursor(dictionary=True)
            
            sql = """
            SELECT
                p.categoria_tema,
                COUNT(*) AS total_preguntas,
                SUM(CASE WHEN r.ok = 1 THEN 0 ELSE 1 END) AS total_errores,
                (SUM(CASE WHEN r.ok = 1 THEN 0 ELSE 1 END) * 100.0 / COUNT(*)) AS porcentaje_error
            FROM examen_respuestas er
            JOIN intentos_examen ie ON er.id_intento = ie.id_intento
            JOIN preguntas p ON er.id_pregunta = p.id_pregunta
            LEFT JOIN respuestas r ON er.id_respuesta_elegida = r.id_respuesta
            WHERE ie.matricula = %s AND p.categoria_tema IS NOT NULL AND er.id_respuesta_elegida IS NOT NULL
            GROUP BY p.categoria_tema
            HAVING total_preguntas > 2 -- Mínimo de preguntas para ser relevante
            ORDER BY porcentaje_error DESC
            LIMIT 5;
            """
            cursor.execute(sql, (matricula,))
            results = cursor.fetchall()
            return results
        
        except Exception as e:
            print(f"Error en get_temas_fallidos_alumno: {e}")
            return [] # Devolver lista vacía en caso de error
        
        finally:
          
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_stats_generales_alumno(matricula):
        """
        Obtiene tiempo promedio, mejor calificación y predicción.
        """
        conn = None
        cursor = None
        try:
            conn = Db.get_connection() 
            cursor = conn.cursor(dictionary=True)
            
            # 1. Tiempo promedio
            sql_tiempo = """
            SELECT AVG(er.tiempo_respuesta_segundos) AS avg_tiempo
            FROM examen_respuestas er
            JOIN intentos_examen ie ON er.id_intento = ie.id_intento
            WHERE ie.matricula = %s AND er.tiempo_respuesta_segundos IS NOT NULL;
            """
            cursor.execute(sql_tiempo, (matricula,))
            avg_tiempo = cursor.fetchone()['avg_tiempo']
            
            # 2. Mejores calificaciones
            sql_calif = """
            SELECT
                MAX(CASE WHEN tipo_test = 'practica' THEN calificacion ELSE 0 END) AS max_practica,
                MAX(CASE WHEN tipo_test = 'final' THEN calificacion ELSE 0 END) AS max_final
            FROM intentos_examen
            WHERE matricula = %s;
            """
            cursor.execute(sql_calif, (matricula,))
            califs = cursor.fetchone()
            
            # 3. Predicción (Promedio ponderado de prácticas)
            sql_pred = """
            SELECT AVG(calificacion) AS avg_practica
            FROM intentos_examen
            WHERE matricula = %s AND tipo_test = 'practica';
            """
            cursor.execute(sql_pred, (matricula,))
            pred = cursor.fetchone()['avg_practica']

            # Formateo para evitar problemas con JSON y Decimal
            return {
                "avg_tiempo_segundos": float(avg_tiempo) if avg_tiempo else 0,
                "max_calif_practica": float(califs['max_practica']) if califs['max_practica'] else 0,
                "max_calif_final": float(califs['max_final']) if califs['max_final'] else 0,
                "prediccion_final": float(pred) if pred else 0
            }
        
        except Exception as e:
            print(f"Error en get_stats_generales_alumno: {e}")
            return { # Devolver valores default en caso de error
                "avg_tiempo_segundos": 0,
                "max_calif_practica": 0,
                "max_calif_final": 0,
                "prediccion_final": 0
            }

        finally:
           
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # --- QUERIES PARA ADMIN ---

    @staticmethod
    def get_temas_dificiles_global():
        """
        Obtiene los temas más difíciles para todos los alumnos.
        """
        conn = None
        cursor = None
        try:
            conn = Db.get_connection() 
            cursor = conn.cursor(dictionary=True)
            sql = """
            SELECT
                p.categoria_tema,
                (SUM(CASE WHEN r.ok = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS porcentaje_acierto
            FROM examen_respuestas er
            JOIN preguntas p ON er.id_pregunta = p.id_pregunta
            LEFT JOIN respuestas r ON er.id_respuesta_elegida = r.id_respuesta
            WHERE p.categoria_tema IS NOT NULL AND er.id_respuesta_elegida IS NOT NULL
            GROUP BY p.categoria_tema
            ORDER BY porcentaje_acierto ASC
            LIMIT 5;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                row['porcentaje_acierto'] = float(row['porcentaje_acierto'])
            return results
        
        except Exception as e:
            print(f"Error en get_temas_dificiles_global: {e}")
            return []

        finally:
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_preguntas_dificiles_global():
        """
        Obtiene las 5 preguntas con menor tasa de aciertos.
        """
        conn = None
        cursor = None
        try:
            conn = Db.get_connection() 
            cursor = conn.cursor(dictionary=True)
            sql = """
            SELECT
                p.reactivo,
                COUNT(*) as total_intentos,
                (SUM(CASE WHEN r.ok = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS porcentaje_acierto
            FROM examen_respuestas er
            JOIN preguntas p ON er.id_pregunta = p.id_pregunta
            LEFT JOIN respuestas r ON er.id_respuesta_elegida = r.id_respuesta
            WHERE er.id_respuesta_elegida IS NOT NULL
            GROUP BY p.id_pregunta, p.reactivo
            HAVING total_intentos > 5 -- Mínimo de respuestas para ser relevante
            ORDER BY porcentaje_acierto ASC
            LIMIT 5;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                row['porcentaje_acierto'] = float(row['porcentaje_acierto'])
            return results

        except Exception as e:
            print(f"Error en get_preguntas_dificiles_global: {e}")
            return []

        finally:
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_stats_generales_admin():
        """
        Obtiene promedios, max/min y total aprobados/reprobados.
        """
        conn = None
        cursor = None
        try:
            conn = Db.get_connection() 
            cursor = conn.cursor(dictionary=True)
            
            # 1. Promedio, Max, Min
            sql_califs = """
            SELECT 
                AVG(calificacion) AS avg_global,
                MAX(calificacion) AS max_calif,
                MIN(calificacion) AS min_calif
            FROM intentos_examen;
            """
            cursor.execute(sql_califs)
            califs = cursor.fetchone()

            # 2. Aprobados / Reprobados (Solo examen 'final')
            sql_status = """
            SELECT
                SUM(CASE WHEN aprobado = 1 THEN 1 ELSE 0 END) AS total_aprobados,
                SUM(CASE WHEN aprobado = 0 THEN 1 ELSE 0 END) AS total_reprobados
            FROM intentos_examen
            WHERE tipo_test = 'final';
            """
            cursor.execute(sql_status)
            status = cursor.fetchone()
            
            return {
                "avg_global": float(califs['avg_global']) if califs['avg_global'] else 0,
                "max_calif": float(califs['max_calif']) if califs['max_calif'] else 0,
                "min_calif": float(califs['min_calif']) if califs['min_calif'] else 0,
                "total_aprobados_final": int(status['total_aprobados']) if status['total_aprobados'] else 0,
                "total_reprobados_final": int(status['total_reprobados']) if status['total_reprobados'] else 0
            }
        
        except Exception as e:
            print(f"Error en get_stats_generales_admin: {e}")
            return {
                "avg_global": 0,
                "max_calif": 0,
                "min_calif": 0,
                "total_aprobados_final": 0,
                "total_reprobados_final": 0
            }

        finally:
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()