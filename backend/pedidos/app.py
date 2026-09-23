from flask import Flask, jsonify
from routes.pedido_routes import pedidos_bp

app = Flask(__name__)
app.register_blueprint(pedidos_bp)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "servicio": "pedidos"}), 200


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
