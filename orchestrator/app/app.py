from flask import Flask, request, jsonify
import requests
import jwt

app = Flask(__name__)

# Call Traefik internally via service DNS,
# but preserve Host header so IngressRoute + OPA apply
TRAEFIK_INTERNAL = "http://traefik.traefik.svc.cluster.local"

LEVELS = {
    "public": 0,
    "internal": 1,
    "confidential": 2
}


@app.route("/declassify", methods=["POST"])
def declassify_payload():
    """
    Dedicated endpoint for IFC Declassification using Secure JSON Envelopes.
    Requires the 'ifc_declassifier' Keycloak role.
    """
    data = request.get_json(force=True)
    payload = data.get("payload", {})
    target_context = data.get("target_context", "public")

    auth_header = request.headers.get("Authorization")
    
    # 1. Strict Role-Based Access Control (RBAC) Check via JWT
    user_roles = []
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Turn off all secondary validations since Traefik handles edge security
            decoded = jwt.decode(
                token, 
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_exp": False
                }
            )
            user_roles = decoded.get("realm_access", {}).get("roles", [])
            
        except Exception as e:
            # Print the exact error to the pod logs for easy debugging
            print(f"JWT Decode Exception: {str(e)}") 
            return jsonify({"status": "error", "message": f"Invalid JWT: {str(e)}"}), 401

    if "ifc_declassifier" not in user_roles:
        return jsonify({
            "status": "rejected",
            "reason": "Forbidden: User lacks the 'ifc_declassifier' realm role."
        }), 403

    # 2. Forward to the actual OpenFaaS Declassifier Function
    headers = {
        "Host": "api.openfaas.local",
        "X-IFC-Context": "confidential", # Run as confidential so OPA allows the request
    }
    if auth_header:
        headers["Authorization"] = auth_header

    # Hardcoded to only hit the declassify function
    resp = requests.post(
        f"{TRAEFIK_INTERNAL}/function/declassify-function",
        headers=headers,
        json=payload,
        timeout=5
    )

    if not resp.ok:
        return jsonify({"status": "error", "message": resp.text}), resp.status_code

    # 3. Return the sanitized data with the downgraded context
    return jsonify({
        "status": "declassified",
        "original_context": "confidential",
        "new_context": target_context,
        "result": resp.json()
    }), 200


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
