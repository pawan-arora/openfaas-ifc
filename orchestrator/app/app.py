from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# IMPORTANT:
# Call Traefik internally via service DNS,
# but preserve Host header so IngressRoute + OPA apply
TRAEFIK_INTERNAL = "http://traefik.traefik.svc.cluster.local"

LEVELS = {
    "public": 0,
    "internal": 1,
    "confidential": 2
}

@app.route("/run-pipeline", methods=["POST"])
def run_pipeline():
    data = request.get_json(force=True)

    pipeline = data.get("pipeline", [])
    payload = data.get("payload", "")
    context = data.get("context", "public")

    # Forward the user's Authorization header (MANDATORY)
    auth_header = request.headers.get("Authorization")

    for step in pipeline:
        headers = {
            # Critical for Traefik routing
            "Host": "api.openfaas.local",

            # IFC context propagation
            "X-IFC-Context": context,
        }

        # Forward JWT so Traefik auth + OPA run
        if auth_header:
            headers["Authorization"] = auth_header

        resp = requests.post(
            f"{TRAEFIK_INTERNAL}/function/{step}",
            headers=headers,
            data=payload,
            timeout=5
        )

        # IFC / auth rejection propagates as 403
        if resp.status_code == 403:
            return jsonify({
                "status": "rejected",
                "at_function": step,
                "context": context
            }), 403

        # Any other error stops the pipeline
        if not resp.ok:
            return jsonify({
                "status": "error",
                "at_function": step,
                "http_status": resp.status_code,
                "message": resp.text
            }), resp.status_code

        # Conservative IFC context update
        # (function label inferred from name: public-function → public)
        step_label = step.split("-")[0]
        if step_label in LEVELS:
            if LEVELS[step_label] > LEVELS[context]:
                context = step_label

        payload = resp.text

    return jsonify({
        "status": "completed",
        "final_context": context,
        "result": payload
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
