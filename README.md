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

 Tecnologías utilizadas

Backend: Flask (Python 3.12)

Base de datos: MySQL

Frontend: HTML, CSS, JavaScript

Estilos: static/css/styles.css

Scripts dinámicos: static/js/exam_timer.js

- Ejecución del proyecto

Instalar dependencias:

pip install -r requirements.txt


Configurar la base de datos en config.py:

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'tu_contraseña'
MYSQL_DB = 'simulador_manejo'


Ejecutar el servidor Flask:

python run.py


Acceder en el navegador a:

http://127.0.0.1:5000

📂 Notas adicionales

El archivo bd_script.txt incluye todos los inserts necesarios (imágenes, preguntas, respuestas).

Las imágenes deben colocarse en:

static/img/senales/


El sistema abre automáticamente el navegador al iniciar Flask.

La autenticación está encriptada con bcrypt.

Conclusión

El Simulador de Examen de Manejo cumple con los objetivos de la materia Simulación, al modelar un sistema interactivo que reproduce el proceso real de evaluación teórica para licencias de conducir, aplicando elementos de aleatoriedad controlada, tiempos de respuesta y validación automática.

© 2025 – Diana Arévalo & Ángel Sánchez
Materia: Simulación
Profesor: David Pérez Tinoco