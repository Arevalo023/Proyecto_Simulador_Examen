# app/routes/auth_routes.py

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, session
from app.models.estudiante_model import (
    obtener_todos_estudiantes,
    crear_estudiante,
    validar_login
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# =========================
# Rutas de debug/pruebas
# =========================
@auth_bp.route("/ping")
def ping_auth():
    return jsonify({"msg": "auth ok"})


@auth_bp.route("/test-db")
def test_db():
    alumnos = obtener_todos_estudiantes()
    return jsonify({
        "status": "ok",
        "count": len(alumnos),
        "data": alumnos
    })


@auth_bp.route("/register-demo")
def register_demo():
    ok = crear_estudiante(
        matricula=12345,
        nombre="Admin",
        paterno="Principal",
        materno="",
        email="Admin@example.com",
        telefono=1234567890,
        password_plano="abc123",
        rol="admin"          # si quieres que tu usuario sea admin cámbialo aquí
    )

    if ok:
        return jsonify({"status": "created"})
    else:
        return jsonify({"status": "error"}), 400


# =========================
# Login / Logout
# =========================

@auth_bp.route("/login", methods=["GET"])
def login_form():
    """
    Muestra la pantalla de login.
    """
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_submit():
    """
    Procesa el login.
    1. Lee matricula y password del form
    2. Valida contra la BD (bcrypt)
    3. Si ok -> guarda info minima en session
    4. Redirige segun rol
    5. Si mal -> flash error y regresa al form
    """
    matricula = request.form.get("matricula", "").strip()
    password = request.form.get("password", "").strip()

    user = validar_login(matricula, password)

    if user is None:
        flash("Credenciales incorrectas", "error")
        return redirect(url_for("auth.login_form"))

    # guardar sesion
    session["usuario_matricula"] = user["matricula"]
    session["usuario_nombre"] = user["nombre"]
    session["usuario_rol"] = user["rol"]

    flash(f"Bienvenido {user['nombre']} ({user['rol']})", "success")

    if user["rol"] == "admin":
        return redirect(url_for("auth.admin_dashboard"))
    else:
        return redirect(url_for("auth.alumno_home"))


@auth_bp.route("/logout")
def logout():
    """
    Limpia la sesion.
    """
    session.clear()
    flash("Sesion cerrada", "info")
    return redirect(url_for("auth.login_form"))


# =========================
# Vistas protegidas
# =========================

@auth_bp.route("/admin/dashboard")
def admin_dashboard():
    """
    Pantalla solo para admin.
    Aquí luego pondremos el dashboard de intentos.
    """
    # validacion rapida de rol
    if session.get("usuario_rol") != "admin":
        flash("Acceso denegado, necesitas rol admin", "error")
        return redirect(url_for("auth.login_form"))

    return render_template(
        "admin_dashboard.html",
        nombre=session.get("usuario_nombre"),
        matricula=session.get("usuario_matricula"),
        rol=session.get("usuario_rol")
    )


@auth_bp.route("/alumno/home")
def alumno_home():
    """
    Pantalla del alumno normal.
    """
    if session.get("usuario_rol") not in ["alumno", "admin"]:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    return render_template(
        "alumno_home.html",
        nombre=session.get("usuario_nombre"),
        matricula=session.get("usuario_matricula"),
        rol=session.get("usuario_rol")
    )
