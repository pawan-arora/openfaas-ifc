from flask import Flask, request, abort
import requests

app = Flask(__name__)

OPA_URL = "http://opa.opa.svc.cluster.local:8181/v1/data/http/authz/allow"

@app.route("/ifc/authorize", methods=["GET", "POST"])
def authorize():
    input_data = {
        "input": {
            "request": {
                "path": request.headers.get("X-Forwarded-Uri"),
                "headers": dict(request.headers)
            }
        }
    }

    r = requests.post(OPA_URL, json=input_data)
    allowed = r.json().get("result", False)

    if not allowed:
        abort(403)

    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
