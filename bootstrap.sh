#!/usr/bin/env bash
set -e

echo "▶ Waiting for Kubernetes..."
until kubectl get nodes >/dev/null 2>&1; do
  sleep 2
done

echo "▶ Applying namespaces"
kubectl apply -f namespaces/

echo "▶ Applying secrets"
kubectl apply -f secrets/

echo "▶ Deploying Keycloak"
helm upgrade --install keycloak ./keycloak \
  -n auth --create-namespace

echo "▶ Deploying OAuth2 Proxy"
kubectl apply -f oauth2-proxy/

echo "▶ Deploying OPA"
kubectl apply -f opa/

echo "▶ Deploying Traefik"
helm upgrade --install traefik ./traefik \
  -n traefik --create-namespace

echo "▶ Deploying OpenFaaS"
helm upgrade --install openfaas ./openfaas \
  -n openfaas --create-namespace

echo "▶ Applying ingress and middleware"
kubectl apply -f ingress/

echo "✅ Cluster bootstrap complete"
