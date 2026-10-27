import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    if os.getenv("BREAK_HEALTH") == "1":
        return jsonify(status="broken"), 503
    return jsonify(status="ok"), 200


@app.get("/")
def index():
    return jsonify(message="Hello from Flask!"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)