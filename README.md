# Simulador de Examen de Manejo

**Proyecto Final de la Materia: Simulación**  
**Universidad Autónoma de Coahuila (UAdeC)**  
**Profesor:** David Pérez Tinoco  

---

## Integrantes del equipo

- **Diana Marcela Arévalo Sifuentes**  
- **Ángel de Jesús Sánchez Jaramillo**

---

## Descripción general

Este proyecto consiste en un **Simulador de Examen Teórico para Licencia de Conducir**, desarrollado con **Flask (Python)** y **MySQL**, que permite a los usuarios practicar y realizar exámenes de manejo, control de intentos y panel de administración.

El sistema está diseñado con **buenas prácticas de arquitectura**, siguiendo una estructura modular con las carpetas:

app/
├── models/
├── routes/
├── static/
│ ├── css/
│ └── js/
├── templates/
├── db.py
└── config.py
---

##  Características principales

- **Inicio de sesión con roles:**  
  - Rol *Alumno*: puede realizar exámenes de práctica y finales.  
  - Rol *Administrador*: puede consultar el historial, estadísticas y controlar el banco de preguntas.

- **Banco de preguntas y respuestas:**  
  - 80 preguntas clasificadas en 8 categorías temáticas.
  - Cada pregunta incluye 4 opciones, con una respuesta correcta.
  - Algunas preguntas incluyen imágenes de señales de tránsito almacenadas en `static/img/senales/`.

- **Simulación de examen real:**  
  - Genera un examen aleatorio con preguntas mixtas de todas las categorías.  
  - Asegura al menos una pregunta de cada tema.  
  - Controla el número máximo de intentos por usuario.  
  - Calcula calificación, aprobación y tiempo total.

- **Dashboard administrativo:**  
  - Muestra estadísticas de desempeño, intentos y promedios.  
  - Permite visualizar resultados y analizar categorías más falladas.

---

## Base de Datos

La base de datos se encuentra definida en el script `bd_script.txt`, que contiene:

1. La estructura completa (`CREATE TABLE ...`)
2. Las relaciones entre tablas (`FOREIGN KEY ...`)
3. Los inserts con los **80 reactivos** del examen, clasificados por tema.

Para ejecutar el script:
```sql
SOURCE bd_script.txt;

Tablas principales:

estudiante

banco_imagenes

preguntas

respuestas

intentos_examen

examen_respuestas

⚠️ Las imágenes de las señales están guardadas en la carpeta:
app/static/img/senales/

⚙️ Tecnologías Utilizadas
Componente	Tecnología
Backend	Python 3.12 (Flask)
Frontend	HTML5, CSS3, JavaScript
Base de datos	MySQL
Encriptación	bcrypt
Librerías	Flask-MySQL, Flask, bcrypt
Entorno	Visual Studio Code
▶️ Ejecución del Proyecto

Instala las dependencias necesarias:

pip install -r requirements.txt


Configura la base de datos en config.py:

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'tu_contraseña'
MYSQL_DB = 'simulador_manejo'


Ejecuta el servidor:

python run.py


El navegador se abrirá automáticamente con la dirección:

http://127.0.0.1:5000

📂 Notas Adicionales

El archivo bd_script.txt contiene todo el esquema de la base de datos y los inserts de las 80 preguntas.

Las imágenes deben almacenarse en:

app/static/img/senales/


Se utilizó bcrypt para el cifrado de contraseñas.

El sistema maneja dos roles de acceso: alumno y admin.

🧠 Funcionalidad del Simulador

Selecciona aleatoriamente preguntas de la base de datos.

Asegura que cada examen tenga al menos una pregunta de cada categoría.

Guarda el historial de intentos, calificaciones y duración.

Permite comparar resultados y mejorar desempeño en cada intento.

🏁 Conclusión

El Simulador de Examen de Manejo replica el comportamiento de una evaluación teórica real para obtener la licencia de conducir.
Aplicando principios de Simulación, el sistema ofrece aleatoriedad controlada, medición de tiempo, validación automática de respuestas y análisis estadístico para los resultados.

© 2025 — Diana Arévalo & Ángel Sánchez
Materia: Simulación
Profesor: David Pérez Tinoco
Universidad Autónoma de Coahuila (UAdeC)