# app/routes/auth_routes.py

from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, session
from app.models.estudiante_model import (
    obtener_todos_estudiantes,
    crear_estudiante,
    validar_login,
    existe_matricula,
    existe_email
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


# =========================
# Registro de alumno
# =========================

@auth_bp.route("/register", methods=["GET"])
def register_form():
    """
    Muestra el formulario de registro de alumno.
    Si ya hay sesion iniciada, lo mando a su home.
    """
    if session.get("usuario_matricula"):
        # ya logueado
        rol_actual = session.get("usuario_rol")
        if rol_actual == "admin":
            return redirect(url_for("auth.admin_dashboard"))
        else:
            return redirect(url_for("auth.alumno_home"))

    return render_template("register.html")


@auth_bp.route("/register", methods=["POST"])
def register_submit():
    """
    Procesa el registro de un nuevo alumno.
    - valida campos obligatorios
    - valida que matricula y email no existan
    - hashea contraseña
    - inserta
    - redirige a login con flash success
    """
    # leer form
    matricula = request.form.get("matricula", "").strip()
    nombre = request.form.get("nombre", "").strip()
    paterno = request.form.get("paterno", "").strip()
    materno = request.form.get("materno", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    password1 = request.form.get("password1", "").strip()
    password2 = request.form.get("password2", "").strip()

    # validaciones basicas
    if not matricula or not nombre or not paterno or not email or not password1 or not password2:
        flash("Faltan campos obligatorios", "error")
        return redirect(url_for("auth.register_form"))

    # contraseñas iguales?
    if password1 != password2:
        flash("Las contraseñas no coinciden", "error")
        return redirect(url_for("auth.register_form"))

    # matricula numerica?
    if not matricula.isdigit():
        flash("La matricula debe ser numerica", "error")
        return redirect(url_for("auth.register_form"))

    # telefono opcional: si viene y no es digitos, error
    if telefono and (not telefono.isdigit()):
        flash("El telefono debe ser numerico", "error")
        return redirect(url_for("auth.register_form"))

    # checar duplicados
    if existe_matricula(matricula):
        flash("Esa matricula ya esta registrada", "error")
        return redirect(url_for("auth.register_form"))

    if existe_email(email):
        flash("Ese correo ya esta registrado", "error")
        return redirect(url_for("auth.register_form"))

    # insertar en BD
    ok = crear_estudiante(
        matricula=int(matricula),
        nombre=nombre,
        paterno=paterno,
        materno=materno,
        email=email,
        telefono=int(telefono) if telefono else None,
        password_plano=password1,
        rol="alumno"   # forzado alumno, no dejo crear admin desde aqui
    )

    if not ok:
        flash("No se pudo crear la cuenta, intenta de nuevo", "error")
        return redirect(url_for("auth.register_form"))

    # éxito
    flash("Cuenta creada, ahora inicia sesion", "success")
    return redirect(url_for("auth.login_form"))


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
