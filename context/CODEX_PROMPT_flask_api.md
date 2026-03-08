# Codex prompt: Flask API for robot control

Copy the block below into Codex.

---

Implement the Flask API in `pi/api_server.py` per **context/AGENTS.MD** and **CONTEXT.md**. Use only Flask and existing stack (pyserial, SerialBridge). Minimal docs only where non-obvious (e.g. shared bridge or threading). **Commit after each section.**

**References:**
- AGENTS.MD: api_server exposes POST /move, POST /stop, GET /telemetry, GET /health; single-letter protocol F/B/L/R/S.
- CONTEXT.md: 9600 baud, commands F/B/L/R/S; run from Pi with `python3 pi/main.py /dev/ttyUSB0`.

**Section 1 – App skeleton + health**  
- Create Flask app in `api_server.py`. Register GET `/health` returning JSON e.g. `{"status": "ok"}`. Add a `run(host, port)` (or use Flask defaults) so `main.py` or a runner can start the server.  
- **Commit:** "api: add Flask app and GET /health"

**Section 2 – Stop**  
- Add POST `/stop`. Handler must call `bridge.send("S")`; accept a shared `SerialBridge` instance (injected at startup or via app config). Return JSON e.g. `{"ok": true}`.  
- **Commit:** "api: add POST /stop"

**Section 3 – Move**  
- Add POST `/move`. Body or query: `direction` one of `forward`|`backward`|`left`|`right`. Map to F/B/L/R and call `bridge.send(cmd)`. Return JSON e.g. `{"ok": true, "direction": "forward"}`. Reject invalid direction with 400.  
- **Commit:** "api: add POST /move"

**Section 4 – Telemetry stub**  
- Add GET `/telemetry`. Return a minimal JSON stub e.g. `{"connected": true}` (connected from bridge state if available). No Arduino telemetry parsing required yet.  
- **Commit:** "api: add GET /telemetry stub"

**Section 5 – Run mode**  
- Allow running the API server from `main.py` (e.g. `python3 pi/main.py --api /dev/ttyUSB0` or env). On `--api`: create SerialBridge, inject into Flask app, run Flask in a thread or as the main loop; do not start the keyboard controller in that mode. Keep keyboard-only mode as default.  
- **Commit:** "api: add --api mode to main.py"

**Deliverable:** With `--api`, the server runs and responds to GET /health, POST /stop, POST /move, GET /telemetry. No extra dependencies; minimal comments.

---
