import os

from flask import Flask, jsonify
from routes.reporte_routes import reportes_bp

app = Flask(__name__)
app.register_blueprint(reportes_bp)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "servicio": "reportes"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
