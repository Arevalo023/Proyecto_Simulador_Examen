import re
import os
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"

SCREENSHOT_DIR = "tests/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def test_flujo_completo_practica(page: Page):
    # Login
    page.goto(f"{BASE_URL}/auth/login")
    page.screenshot(path=f"{SCREENSHOT_DIR}/01_login_page.png")

    page.fill("#matricula", "20017531")
    page.fill("#password", "123")
    page.click("button[type='submit']")

    expect(page.locator("body")).to_contain_text("Bienvenido")
    page.screenshot(path=f"{SCREENSHOT_DIR}/02_dashboard_inicial.png")

    # Guardar intentos previos
    intento_prev = page.locator("text=Práctica:").inner_text().strip()
    prev = int(re.findall(r"Práctica:\s*(\d+)", intento_prev)[0])

    # Iniciar práctica
    page.click("a[href*='/exam/start/practica']")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{SCREENSHOT_DIR}/03_inicio_practica.png")

    # Responder 20 preguntas
    for i in range(20):
        expect(page.locator("h2.card-title")).to_contain_text(f"Pregunta {i+1}")
        page.screenshot(path=f"{SCREENSHOT_DIR}/pregunta_{i+1:02}.png")
        page.locator("input[name='id_respuesta']").first.click()
        page.click("#btnResponder")
        if i < 19:
            page.wait_for_selector(f"text=Pregunta {i+2}")

    # Validar resultados
    expect(page).to_have_url(re.compile(r"/exam/finish"))
    expect(page.locator("body")).to_contain_text("Resultado")
    page.screenshot(path=f"{SCREENSHOT_DIR}/04_resultados_finales.png")

    # Volver al dashboard
    page.goto(f"{BASE_URL}/auth/alumno/home")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{SCREENSHOT_DIR}/05_dashboard_post_examen.png")

    # Validar decremento de intentos
    intento_new = page.locator("text=Práctica:").inner_text().strip()
    new = int(re.findall(r"Práctica:\s*(\d+)", intento_new)[0])
    assert new == prev - 1
    page.screenshot(path=f"{SCREENSHOT_DIR}/06_intentos_actualizados.png")

    # Validar KPIs
    expect(page.locator("#stat-max-practica")).not_to_have_text("...")
    expect(page.locator("#stat-avg-tiempo")).not_to_have_text("...")
    expect(page.locator("#stat-prediccion")).not_to_have_text("...")
    page.screenshot(path=f"{SCREENSHOT_DIR}/07_kpis_actualizados.png")

    # Bajar al historial
    page.locator("text=Historial de Práctica").scroll_into_view_if_needed()

    historial_items = page.locator(".history-item")
    expect(historial_items.first).to_be_visible()

    # Validar que haya porcentaje
    expect(historial_items.first).to_contain_text("%")

    page.screenshot(path=f"{SCREENSHOT_DIR}/08_historial_actualizado.png")
