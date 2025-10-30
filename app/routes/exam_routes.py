# app/routes/exam_routes.py

from flask import Blueprint, jsonify

exam_bp = Blueprint("exam", __name__, url_prefix="/exam")

@exam_bp.route("/ping")
def ping_exam():
    return jsonify({"msg": "exam ok"})
