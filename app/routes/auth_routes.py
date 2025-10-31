# app/routes/auth_routes.py

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, session
from app.models.estudiante_model import (
    obtener_todos_estudiantes,
    crear_estudiante,
    validar_login,
    existe_matricula,
    existe_email
)
from app.models.exam_model import (
    contar_intentos,
    obtener_historial_intentos
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------
# Debug
# -------------------------
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


# -------------------------
# Registro
# -------------------------
@auth_bp.route("/register", methods=["GET"])
def register_form():
    if session.get("usuario_matricula"):
        rol_actual = session.get("usuario_rol")
        if rol_actual == "admin":
            return redirect(url_for("auth.admin_dashboard"))
        else:
            return redirect(url_for("auth.alumno_home"))

    return render_template("register.html")


@auth_bp.route("/register", methods=["POST"])
def register_submit():
    matricula = request.form.get("matricula", "").strip()
    nombre = request.form.get("nombre", "").strip()
    paterno = request.form.get("paterno", "").strip()
    materno = request.form.get("materno", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password1 = request.form.get("password1", "").strip()
    password2 = request.form.get("password2", "").strip()

    if not matricula or not nombre or not paterno or not email or not password1 or not password2:
        flash("Faltan campos obligatorios", "error")
        return redirect(url_for("auth.register_form"))

    if password1 != password2:
        flash("Las contraseñas no coinciden", "error")
        return redirect(url_for("auth.register_form"))

    if not matricula.isdigit():
        flash("La matricula debe ser numerica", "error")
        return redirect(url_for("auth.register_form"))

    if telefono and (not telefono.isdigit()):
        flash("El telefono debe ser numerico", "error")
        return redirect(url_for("auth.register_form"))

    if existe_matricula(matricula):
        flash("Esa matricula ya esta registrada", "error")
        return redirect(url_for("auth.register_form"))

    if existe_email(email):
        flash("Ese correo ya esta registrado", "error")
        return redirect(url_for("auth.register_form"))

    ok = crear_estudiante(
        matricula=int(matricula),
        nombre=nombre,
        paterno=paterno,
        materno=materno,
        email=email,
        telefono=int(telefono) if telefono else None,
        password_plano=password1,
        rol="alumno"
    )

    if not ok:
        flash("No se pudo crear la cuenta, intenta de nuevo", "error")
        return redirect(url_for("auth.register_form"))

    flash("Cuenta creada, ahora inicia sesion", "success")
    return redirect(url_for("auth.login_form"))


# -------------------------
# Login / Logout
# -------------------------
@auth_bp.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_submit():
    matricula = request.form.get("matricula", "").strip()
    password = request.form.get("password", "").strip()

    user = validar_login(matricula, password)

    if user is None:
        flash("Credenciales incorrectas", "error")
        return redirect(url_for("auth.login_form"))

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
    Si el usuario intenta cerrar sesión en medio de un examen activo,
    le mostramos una pagina de confirmacion.
    """
    examen_id = session.get("examen_actual_id")
    examen_tipo = session.get("examen_actual_tipo")

    if examen_id and examen_tipo:
        # aún hay examen en progreso
        return render_template(
            "logout_confirm.html",
            examen_tipo=examen_tipo
        )

    session.clear()
    flash("Sesion cerrada", "info")
    return redirect(url_for("auth.login_form"))


@auth_bp.route("/logout/force", methods=["POST"])
def logout_force():
    """
    El alumno aceptó perder el intento.
    Limpiamos la sesion completa.
    (El intento ya queda en BD como usado.)
    """
    session.clear()
    flash("Sesion cerrada. Este intento se consumio.", "info")
    return redirect(url_for("auth.login_form"))


# -------------------------
# Admin Dashboard
# -------------------------
@auth_bp.route("/admin/dashboard")
def admin_dashboard():
    if session.get("usuario_rol") != "admin":
        flash("Acceso denegado, necesitas rol admin", "error")
        return redirect(url_for("auth.login_form"))

    return render_template(
        "admin_dashboard.html",
        nombre=session.get("usuario_nombre"),
        matricula=session.get("usuario_matricula"),
        rol=session.get("usuario_rol")
    )


# -------------------------
# Home del alumno
# -------------------------
@auth_bp.route("/alumno/home")
def alumno_home():
    if session.get("usuario_rol") not in ["alumno", "admin"]:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    matricula = session.get("usuario_matricula")

    usados_practica = contar_intentos(matricula, "practica")
    limite_practica = 6
    restantes_practica = max(limite_practica - usados_practica, 0)

    historial_practica = obtener_historial_intentos(matricula, "practica")

    usados_final = contar_intentos(matricula, "final")
    limite_final = 3
    restantes_final = max(limite_final - usados_final, 0)

    historial_final = obtener_historial_intentos(matricula, "final")

    return render_template(
        "alumno_home.html",
        nombre=session.get("usuario_nombre"),
        matricula=matricula,
        rol=session.get("usuario_rol"),

        usados_practica=usados_practica,
        restantes_practica=restantes_practica,
        historial_practica=historial_practica,

        usados_final=usados_final,
        restantes_final=restantes_final,
        historial_final=historial_final,
    )
