# run.py

from app import create_app
import threading
import webbrowser
import os

app = create_app()

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:5000/auth/login")

if __name__ == "__main__":
    # solo abrir navegador si NO estamos en el proceso recargador
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, abrir_navegador).start()

    app.run(debug=True)
