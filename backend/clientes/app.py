from flask import Flask, jsonify
from routes.cliente_routes import clientes_bp

app = Flask(__name__)
app.register_blueprint(clientes_bp)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "servicio": "clientes"}), 200


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
