from fastapi import FastAPI, HTTPException
from kubernetes import client, config

app = FastAPI()

# Load in-cluster Kubernetes config
config.load_incluster_config()

apps_v1 = client.AppsV1Api()

OPENFAAS_FN_NAMESPACE = "openfaas-fn"

@app.get("/resolve")
def resolve(function: str):
    try:
        dep = apps_v1.read_namespaced_deployment(
            name=function,
            namespace=OPENFAAS_FN_NAMESPACE
        )
    except client.exceptions.ApiException as e:
        raise HTTPException(
            status_code=404,
            detail=f"Function deployment '{function}' not found"
        )

    annotations = dep.metadata.annotations or {}
    label = annotations.get("ifc/label", "public")

    return {
        "function": function,
        "ifc_label": label
    }
