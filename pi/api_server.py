from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


def run_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    app.run(host=host, port=port)

