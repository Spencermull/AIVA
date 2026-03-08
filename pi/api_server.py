from flask import Flask, jsonify, request

app = Flask(__name__)

DIRECTION_TO_CMD = {
    "forward": "F",
    "backward": "B",
    "left": "L",
    "right": "R",
}


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


@app.post("/move")
def move():
    bridge = app.config.get("bridge")
    if bridge is None:
        return jsonify({"ok": False, "error": "bridge not configured"}), 503

    direction = request.args.get("direction")
    if direction is None:
        payload = request.get_json(silent=True) or {}
        direction = payload.get("direction")

    if not isinstance(direction, str):
        return jsonify({"ok": False, "error": "invalid direction"}), 400

    direction = direction.strip().lower()
    cmd = DIRECTION_TO_CMD.get(direction)
    if cmd is None:
        return jsonify({"ok": False, "error": "invalid direction"}), 400

    bridge.send(cmd)
    return jsonify({"ok": True, "direction": direction})


def run_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    app.run(host=host, port=port)

