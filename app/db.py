# app/db.py

import mysql.connector
from mysql.connector import Error
from flask import current_app

class Db:
    @staticmethod
    def get_connection():
        """
        Regresa una conexion nueva a MySQL usando la config cargada en Flask.
        Acordate de cerrar conn y cursor cuando termines.
        """
        try:
            conn = mysql.connector.connect(
                host=current_app.config["DB_HOST"],
                user=current_app.config["DB_USER"],
                password=current_app.config["DB_PASSWORD"],
                database=current_app.config["DB_NAME"],
                port=current_app.config["DB_PORT"],
                autocommit=False
            )
            return conn
        except Error as e:
            print("Error al conectar a MySQL:", e)
            raise e
