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
    calcular_calificacion_y_cerrar_intento
)

exam_bp = Blueprint("exam", __name__, url_prefix="/exam")


# -----------------------
# Helpers internos
# -----------------------

def requiere_login_alumno():
    """
    Valida que haya sesion activa y que sea alumno o admin.
    Regresa (matricula, rol) o (None, None) si no hay permiso.
    """
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
    1. Checar login
    2. Revisar limite de 6 intentos
    3. Crear intento_examen tipo 'practica'
    4. Seleccionar 20 preguntas random
    5. Guardarlas en examen_respuestas
    6. Guardar en session info de control (id_intento y timestamp inicio)
    7. Redirigir a la primera pregunta
    """
    matricula, rol = requiere_login_alumno()
    if matricula is None:
        flash("Inicia sesion primero", "error")
        return redirect(url_for("auth.login_form"))

    # checar limite (6)
    num_intentos = contar_intentos(matricula, "practica")
    if num_intentos >= 6:
        flash("Ya usaste tus 6 intentos de practica", "error")
        return redirect(url_for("auth.alumno_home"))

    # crear intento
    id_intento = crear_intento(matricula, "practica")
    if id_intento is None:
        flash("No se pudo crear el intento", "error")
        return redirect(url_for("auth.alumno_home"))

    # seleccionar 20 preguntas aleatorias
    preguntas = seleccionar_preguntas_aleatorias(20)

    if len(preguntas) < 20:
        flash("No hay suficientes preguntas en el banco (se necesitan 20)", "error")
        return redirect(url_for("auth.alumno_home"))

    ok = registrar_preguntas_en_intento(id_intento, preguntas)
    if not ok:
        flash("Error al preparar el examen", "error")
        return redirect(url_for("auth.alumno_home"))

    # guardamos en session el tracking de este examen
    session["examen_actual_id"] = id_intento
    session["examen_actual_tipo"] = "practica"
    session["examen_inicio_ts"] = time.time()

    # primera pregunta (index 0)
    return redirect(url_for("exam.show_question", index=0))


# -----------------------
# MOSTRAR PREGUNTA N
# -----------------------

@exam_bp.route("/question/<int:index>", methods=["GET"])
def show_question(index):
    """
    Muestra la pregunta #index del examen actual en session.
    Renderiza template exam_question.html
    """
    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")

    if not id_intento or not tipo_test:
        flash("No tienes un examen activo", "error")
        return redirect(url_for("auth.alumno_home"))

    estado = obtener_estado_pregunta(id_intento, index)
    if estado is None:
        # index fuera de rango -> significa que ya no hay mas preguntas
        return redirect(url_for("exam.finish_exam"))

    # timestamp de inicio de ESTA pregunta para controlar el minuto
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
    """
    Procesa la respuesta de la pregunta actual:
    - lee id_pregunta y id_respuesta_elegida del form
    - calcula si se contesto dentro de 60s
    - guarda en examen_respuestas
    - redirige a la siguiente pregunta
    """
    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")
    index_actual = session.get("pregunta_index", 0)
    ts_inicio = session.get("pregunta_start_ts", time.time())

    if not id_intento or not tipo_test:
        flash("No tienes un examen activo", "error")
        return redirect(url_for("auth.alumno_home"))

    # leer lo que viene del form
    id_pregunta = request.form.get("id_pregunta")
    id_respuesta_elegida = request.form.get("id_respuesta")
    # si el alumno no marcó nada, id_respuesta_elegida será None -> cuenta como mala

    # calcular tiempo
    ahora = time.time()
    elapsed = int(ahora - ts_inicio)

    # contestó a tiempo?
    contesto_a_tiempo = (elapsed <= 60)

    # guardar en BD
    guardar_respuesta_de_pregunta(
        id_intento=id_intento,
        id_pregunta=id_pregunta,
        id_respuesta_elegida=id_respuesta_elegida,
        contesto_a_tiempo=contesto_a_tiempo,
        tiempo_seg=elapsed
    )

    # siguiente pregunta
    siguiente = int(index_actual) + 1
    return redirect(url_for("exam.show_question", index=siguiente))


# -----------------------
# TERMINAR EXAMEN
# -----------------------

@exam_bp.route("/finish")
def finish_exam():
    """
    Calcula la calificacion final, marca aprobado o no, limpia session parcial
    y muestra la pantalla de resultado.
    """
    id_intento = session.get("examen_actual_id")
    tipo_test = session.get("examen_actual_tipo")

    if not id_intento or not tipo_test:
        flash("No hay examen para cerrar", "error")
        return redirect(url_for("auth.alumno_home"))

    resultado = calcular_calificacion_y_cerrar_intento(id_intento, tipo_test)

    # limpiar datos de examen en session para que no reusen
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
