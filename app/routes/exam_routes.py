# app/routes/exam_routes.py

from flask import Blueprint, request, redirect, url_for, session, render_template, flash
import time

from app.models.exam_model import (
    contar_intentos,
    crear_intento,
    seleccionar_preguntas_aleatorias,
    registrar_preguntas_en_intento,
    obtener_estado_pregunta,
    guardar_respuesta_de_pregunta,
    calcular_calificacion_y_cerrar_intento,
    obtener_detalle_intento
)

exam_bp = Blueprint("exam", __name__, url_prefix="/exam")


# -----------------------
# Helper: validar sesión de alumno/admin
# -----------------------
def requiere_login_alumno():
    rol = session.get("usuario_rol")
    mat = session.get("usuario_matricula")
    if rol not in ["alumno", "admin"] or mat is None:
        return (None, None)
    return (mat, rol)


# -----------------------
# INICIAR EXAMEN PRACTICA
# -----------------------
@exam_bp.route("/start/practica")
def start_practica():
    """
    1. Valida login
    2. Checa limite 6 intentos
    3. Crea intento tipo 'practica'
    4. Selecciona 20 preguntas aleatorias
    5. Las registra en examen_respuestas
    6. Guarda en session datos de control
    7. Redirige a pregunta 0
    """
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    usados = contar_intentos(matricula, "practica")
    if usados >= 6:
        flash("Ya usaste tus 6 intentos de practica", "error")
        return redirect(url_for("auth.alumno_home"))

    id_intento = crear_intento(matricula, "practica")
    if id_intento is None:
        flash("No se pudo crear el intento de practica", "error")
        return redirect(url_for("auth.alumno_home"))

    preguntas = seleccionar_preguntas_aleatorias(20)
    if len(preguntas) < 20:
        flash("No hay suficientes preguntas (necesitamos 20)", "error")
        return redirect(url_for("auth.alumno_home"))

    ok = registrar_preguntas_en_intento(id_intento, preguntas)
    if not ok:
        flash("Error al preparar preguntas de practica", "error")
        return redirect(url_for("auth.alumno_home"))

    session["examen_actual_id"] = id_intento
    session["examen_actual_tipo"] = "practica"
    session["examen_inicio_ts"] = time.time()

    # primera pregunta
    return redirect(url_for("exam.show_question", index=0))


# -----------------------
# INICIAR EXAMEN FINAL
# -----------------------
@exam_bp.route("/start/final")
def start_final():
    """
    Igual que practica pero:
    - límite 3 intentos
    - 40 preguntas
    - tipo_test 'final'
    """
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    usados = contar_intentos(matricula, "final")
    if usados >= 3:
        flash("Ya usaste tus 3 intentos del examen final", "error")
        return redirect(url_for("auth.alumno_home"))

    id_intento = crear_intento(matricula, "final")
    if id_intento is None:
        flash("No se pudo crear el intento final", "error")
        return redirect(url_for("auth.alumno_home"))

    preguntas = seleccionar_preguntas_aleatorias(40)
    if len(preguntas) < 40:
        flash("No hay suficientes preguntas (necesitamos 40)", "error")
        return redirect(url_for("auth.alumno_home"))

    ok = registrar_preguntas_en_intento(id_intento, preguntas)
    if not ok:
        flash("Error al preparar preguntas del examen final", "error")
        return redirect(url_for("auth.alumno_home"))

    session["examen_actual_id"] = id_intento
    session["examen_actual_tipo"] = "final"
    session["examen_inicio_ts"] = time.time()

    return redirect(url_for("exam.show_question", index=0))


# -----------------------
# MOSTRAR PREGUNTA N
# -----------------------
@exam_bp.route("/question/<int:index>", methods=["GET"])
def show_question(index):
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")

    if not id_intento or not tipo_test:
        flash("No tienes un examen activo", "error")
        return redirect(url_for("auth.alumno_home"))

    estado = obtener_estado_pregunta(id_intento, index)
    if estado is None:
        # ya no hay más preguntas - terminar examen
        return redirect(url_for("exam.finish_exam"))

    # guardamos marca de tiempo de ESTA pregunta
    session["pregunta_start_ts"] = time.time()
    session["pregunta_index"] = index

    return render_template(
        "exam_question.html",
        intento_id=id_intento,
        tipo_test=tipo_test,
        total=estado["total"],
        index_actual=estado["index"],
        pregunta=estado["pregunta"],
        opciones=estado["opciones"]
    )


# -----------------------
# RECIBIR RESPUESTA
# -----------------------
@exam_bp.route("/answer", methods=["POST"])
def submit_answer():
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")
    index_actual = session.get("pregunta_index", 0)
    ts_inicio = session.get("pregunta_start_ts", time.time())

    if not id_intento or not tipo_test:
        flash("No tienes un examen activo", "error")
        return redirect(url_for("auth.alumno_home"))

    id_pregunta = request.form.get("id_pregunta")
    id_respuesta_elegida = request.form.get("id_respuesta")  # puede venir vacio

    ahora = time.time()
    elapsed = int(ahora - ts_inicio)

    contesto_a_tiempo = (elapsed <= 60)

    guardar_respuesta_de_pregunta(
        id_intento=id_intento,
        id_pregunta=id_pregunta,
        id_respuesta_elegida=id_respuesta_elegida,
        contesto_a_tiempo=contesto_a_tiempo,
        tiempo_seg=elapsed
    )

    siguiente = int(index_actual) + 1
    return redirect(url_for("exam.show_question", index=siguiente))


# -----------------------
# TERMINAR EXAMEN
# -----------------------
@exam_bp.route("/finish")
def finish_exam():
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")

    if not id_intento or not tipo_test:
        flash("No hay examen para cerrar", "error")
        return redirect(url_for("auth.alumno_home"))

    resultado = calcular_calificacion_y_cerrar_intento(id_intento, tipo_test)

    # limpiar sesión de examen activo
    session.pop("examen_actual_id", None)
    session.pop("examen_actual_tipo", None)
    session.pop("examen_inicio_ts", None)
    session.pop("pregunta_start_ts", None)
    session.pop("pregunta_index", None)

    if not resultado:
        flash("Error al calcular resultado", "error")
        return redirect(url_for("auth.alumno_home"))

    return render_template(
        "exam_result.html",
        tipo_test=tipo_test,
        total_preguntas=resultado["total_preguntas"],
        correctas=resultado["correctas"],
        calificacion=resultado["calificacion"],
        aprobado=resultado["aprobado"]
    )

# -----------------------
# REVISAR DETALLE DE UN INTENTO
# -----------------------
@exam_bp.route("/review/<int:id_intento>")
def review_attempt(id_intento):
    """
    Muestra la revisión completa de un intento:
    - Datos generales (fecha, calificación, aprobado)
    - Lista de preguntas con:
        * texto
        * imagen
        * opción correcta
        * opción elegida
        * indicador correcta/incorrecta
        * si fue fuera de tiempo
    Solo permite ver intentos del propio alumno.
    """
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    detalle = obtener_detalle_intento(id_intento, matricula=matricula)
    if not detalle:
        flash("No se encontró el intento o no te pertenece", "error")
        return redirect(url_for("auth.alumno_home"))

    intento = detalle["intento"]
    preguntas = detalle["preguntas"]

    return render_template(
        "exam_review.html",
        intento=intento,
        preguntas=preguntas
    )

