from flask import Flask, jsonify
from routes.producto_routes import productos_bp

app = Flask(__name__)
app.register_blueprint(productos_bp)


@app.get("/health")
def health():
    """Endpoint de salud — útil para docker-compose healthcheck y para el gateway."""
    return jsonify({"status": "ok", "servicio": "catalogo"}), 200


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
