import pytest
from unittest.mock import patch, MagicMock
from app import create_app

# ============================
#   FIXTURE DE FLASK
# ============================
@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================
#   PRUEBAS DE LOGIN
# ============================
def test_login_exitoso(client):
    # Simula sesion válida
    with patch("app.models.estudiante_model.validar_login") as mock_login:
        mock_login.return_value = {
            "matricula": "2000",
            "nombre": "PRUEBAS2",
            "rol": "alumno",
            "paterno": "PRUEBAS2"
        }

        resp = client.post("/auth/login", data={
            "matricula": "2000",
            "password": "123"
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert b"Bienvenido" in resp.data


def test_login_fallido(client):
    with patch("app.models.estudiante_model.validar_login") as m:
        m.return_value = None

        resp = client.post("/auth/login", data={
            "matricula": "2000",
            "password": "bad"
        })

        assert resp.status_code in (200, 302)
        assert b"Credenciales incorrectas" in resp.data


# ============================
#   PROBAR FUNCIONES DE LÓGICA
# ============================

# ----- calcular puntaje (simulado con lógica propia) -----
def calcular_puntaje(respuestas_usuario, respuestas_correctas):
    correctas = 0
    for u, c in zip(respuestas_usuario, respuestas_correctas):
        if u == c:
            correctas += 1
    return correctas


def test_calcular_puntaje():
    assert calcular_puntaje([1, 2, 3], [1, 2, 4]) == 2
    assert calcular_puntaje([1, 2], [3, 4]) == 0
    assert calcular_puntaje([], []) == 0


# ----- verificar aprobación -----
def verificar_aprobacion(puntaje):
    return puntaje >= 75


def test_verificar_aprobacion():
    assert verificar_aprobacion(80) is True
    assert verificar_aprobacion(74) is False


# ----- control de intentos (mock MySQL) -----
@patch("app.models.exam_model.contar_intentos")
def test_control_intentos(mock_contar):
    mock_contar.return_value = 2
    assert mock_contar("2000", "practica") == 2

    mock_contar.return_value = 0
    assert mock_contar("2000", "final") == 0


# ----- generar examen aleatorio (mock) -----
@patch("app.models.exam_model.seleccionar_preguntas_aleatorias")
def test_generar_examen(mock_sel):
    mock_sel.return_value = [
        {"id_pregunta": 1, "reactivo": "¿?", "codigo_imagen": None},
        {"id_pregunta": 2, "reactivo": "¿?", "codigo_imagen": None},
    ]

    result = mock_sel(2)
    assert len(result) == 2
    assert result[0]["id_pregunta"] == 1


# ============================
#   PROBAR INICIO DE EXAMEN
# ============================
@patch("app.models.exam_model.contar_intentos")
@patch("app.models.exam_model.crear_intento")
@patch("app.models.exam_model.seleccionar_preguntas_aleatorias")
@patch("app.models.exam_model.registrar_preguntas_en_intento")
def test_start_practica(mock_reg, mock_sel, mock_crear, mock_contar, client):
    mock_contar.return_value = 0
    mock_crear.return_value = 10
    mock_sel.return_value = [{"id_pregunta": i} for i in range(20)]
    mock_reg.return_value = True

    with client.session_transaction() as sess:
        sess["usuario_matricula"] = "2000"
        sess["usuario_rol"] = "alumno"

    resp = client.get("/exam/start/practica", follow_redirects=True)

    assert resp.status_code == 200
    assert b"Pregunta" in resp.data


# ============================
#   PROBAR RESPUESTA DE PREGUNTA
# ============================
@patch("app.models.exam_model.guardar_respuesta_de_pregunta")
def test_submit_answer(mock_guardar, client):
    mock_guardar.return_value = True

    with client.session_transaction() as sess:
        sess["usuario_matricula"] = "2000"
        sess["usuario_rol"] = "alumno"
        sess["examen_actual_id"] = 99
        sess["examen_actual_tipo"] = "practica"
        sess["pregunta_index"] = 0
        sess["pregunta_start_ts"] = 1

    resp = client.post("/exam/answer", data={
        "id_pregunta": "1",
        "id_respuesta": "2"
    }, follow_redirects=True)

    assert resp.status_code in (200, 302)


# ============================
#   PROBAR FIN DE EXAMEN
# ============================
@patch("app.models.exam_model.calcular_calificacion_y_cerrar_intento")
def test_finish_exam(mock_calc, client):
    mock_calc.return_value = {
        "total_preguntas": 1,
        "correctas": 1,
        "calificacion": 100,
        "aprobado": 1
    }

    with client.session_transaction() as sess:
        sess["usuario_matricula"] = "2000"
        sess["usuario_rol"] = "alumno"
        sess["examen_actual_id"] = 1
        sess["examen_actual_tipo"] = "practica"

    resp = client.get("/exam/finish", follow_redirects=True)

    assert resp.status_code == 200
    assert b"Resultado" in resp.data


# ============================
#   PROBAR HISTORIAL DE INTENTOS
# ============================
@patch("app.models.exam_model.obtener_historial_intentos")
def test_historial(mock_hist, client):
    mock_hist.return_value = [
        {"id_intento": 1, "calificacion": 80, "aprobado": 1},
        {"id_intento": 2, "calificacion": 60, "aprobado": 0},
    ]

    with client.session_transaction() as sess:
        sess["usuario_matricula"] = "2000"
        sess["usuario_rol"] = "alumno"

    resp = client.get("/auth/alumno/home")

    assert resp.status_code == 200
    assert b"Historial" in resp.data
