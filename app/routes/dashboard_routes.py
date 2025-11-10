# app/routes/dashboard_routes.py

from flask import Blueprint, jsonify, session, abort
from app.models.dashboard_model import DashboardModel
from functools import wraps

# Crear un Blueprint para las rutas del dashboard
dashboard_bp = Blueprint('dashboard_bp', __name__)

# --- Decoradores de seguridad ---


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if 'usuario_matricula' not in session: 
            return abort(401) # No autorizado
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if 'usuario_rol' not in session or session['usuario_rol'] != 'admin':
            return abort(403) # Prohibido
        return f(*args, **kwargs)
    return decorated_function


# --- ENDPOINTS PARA ALUMNO ---

@dashboard_bp.route('/dashboard/alumno/datos')
@login_required
def get_alumno_data():
    """
    Endpoint JSON para el dashboard del alumno.
    """
    try:
       
        matricula = session['usuario_matricula']
        
        temas_fallidos = DashboardModel.get_temas_fallidos_alumno(matricula)
        stats = DashboardModel.get_stats_generales_alumno(matricula)
        
        return jsonify({
            "temas_fallidos": temas_fallidos,
            "stats_generales": stats
        })
    except Exception as e:
        print(f"Error en get_alumno_data: {e}")
        return jsonify({"error": "Error al obtener datos del alumno"}), 500


# --- ENDPOINTS PARA ADMIN ---

@dashboard_bp.route('/dashboard/admin/datos')
@login_required
@admin_required
def get_admin_data():
    """
    Endpoint JSON para el dashboard del administrador.
    """
    try:
        temas_dificiles = DashboardModel.get_temas_dificiles_global()
        preguntas_dificiles = DashboardModel.get_preguntas_dificiles_global()
        stats = DashboardModel.get_stats_generales_admin()
        
        return jsonify({
            "temas_dificiles": temas_dificiles,
            "preguntas_dificiles": preguntas_dificiles,
            "stats_generales": stats
        })
    except Exception as e:
        print(f"Error en get_admin_data: {e}")
        return jsonify({"error": "Error al obtener datos del administrador"}), 500