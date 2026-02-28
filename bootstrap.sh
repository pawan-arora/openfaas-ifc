#!/usr/bin/env bash
set -e

echo "▶ 1/9 Waiting for Kubernetes cluster to be ready..."
until kubectl get nodes >/dev/null 2>&1; do
  sleep 2
done
echo "✔ Kubernetes is ready."

echo "▶ 2/9 Applying namespaces..."
kubectl apply -f namespaces/

echo "▶ 3/9 Applying secrets..."
kubectl apply -f secrets/

echo "▶ 4/9 Deploying Traefik (Gateway/Ingress)..."
# Deployed early so its Custom Resource Definitions (CRDs) like IngressRoute are available
helm upgrade --install traefik ./traefik \
  -n traefik --create-namespace
echo "⏳ Waiting for Traefik CRDs to register..."
sleep 5 

echo "▶ 5/9 Deploying Keycloak (Auth)..."
helm upgrade --install keycloak ./keycloak \
  -n auth --create-namespace

echo "▶ 6/9 Deploying OAuth2 Proxy..."
kubectl apply -f oauth2-proxy/

echo "▶ 7/9 Deploying Open Policy Agent (OPA)..."
kubectl apply -f opa/

echo "▶ 8/9 Deploying OpenFaaS Core & Enforcer/Resolver..."
helm upgrade --install openfaas ./openfaas \
  -n openfaas --create-namespace

echo "▶ 9/9 Applying Ingress and Traefik Middleware..."
kubectl apply -f ingress/

# Optionally deploy the Orchestrator here if you have a folder for it
# echo "▶ Deploying Orchestrator..."
# kubectl apply -f orchestrator/k8s/

echo "✅ Cluster bootstrap complete!"
echo "Run 'kubectl get pods -A -w' to watch the pods spin up."