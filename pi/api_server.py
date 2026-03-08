from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/stop")
def stop():
    bridge = app.config.get("bridge")
    if bridge is None:
        return jsonify({"ok": False, "error": "bridge not configured"}), 503

    bridge.send("S")
    return jsonify({"ok": True})


def run_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    app.run(host=host, port=port)

