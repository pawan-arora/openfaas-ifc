# OpenFaaS IFC

 An advanced Information Flow Control (IFC) enforcement framework for OpenFaaS using Keycloak, Traefik, Open Policy Agent (OPA), and a custom Python pipeline orchestrator.

## Overview

This project explores how Information Flow Control (IFC) can be integrated into OpenFaaS to prevent unsafe information flows between serverless functions. 

Traditional OpenFaaS security focuses heavily on boundary authentication and access control. This project extends that model by introducing a **Zero Trust Data Plane** that includes:
- Dynamic security labels for functions via Kubernetes annotations (`ifc/label`).
- User clearance levels embedded securely in Keycloak JWT tokens.
- Real-time flow validation across function pipelines using OPA.
- Controlled, cryptographically masked declassification support via Secure JSON Envelopes.

The primary goal is to prevent accidental data leaks and enforce strict data governance when composing distributed FaaS functions.

---

## Architecture

The system is fully containerized and runs on Kubernetes, integrating the following core components:

- **Keycloak (Auth):** Acts as the Identity Provider (IdP), embedding custom `ifc_clearance` claims and roles (`ifc_declassifier`) into standard JWTs.
- **Traefik (Gateway):** Handles edge routing, acting as a reverse proxy that intercepts requests and passes them to the authorization middleware.
- **IFC Enforcer:** A lightweight Flask microservice that acts as the Traefik ForwardAuth middleware, securely passing request contexts to OPA.
- **Open Policy Agent (OPA):** The decision engine. It evaluates Rego policies to ensure the subject's clearance level is mathematically greater than or equal to the target function's required clearance.
-  **IFC Resolver:** A FastAPI microservice running on port 8000 that OPA queries in real-time via `http.send`. It dynamically reads Kubernetes `ifc/label` annotations from OpenFaaS deployments, eliminating the need for hardcoded security policies.
-  **Custom Orchestrator:** A dedicated Flask application that executes function pipelines, conservatively upgrades pipeline sensitivity contexts, and provides a heavily audited endpoint for data declassification.

---

## Security Model

The system enforces strict mathematical information flow using defined security clearance levels:

* `0` - **Public**: Universally accessible data and functions.
* `1` - **Internal**: Restricted to authenticated organizational users.
* `2` - **Confidential**: Highly sensitive data requiring strict clearance to access or process.

**Rules Enforced (No Read Up, No Write Down):**
1. A user can only invoke functions at or below their personal Keycloak `ifc_clearance` level.
2. Pipelines are automatically rejected if they attempt to flow data from a higher sensitivity context to a lower one without explicit, authorized declassification.
3. Declassification is treated as a privileged action, requiring specific Role-Based Access Control (RBAC).

---

## Example Scenarios

### Without IFC
A developer mistakenly chains a `confidential` database lookup into a `public` logging function, silently leaking sensitive financial data to an insecure endpoint.

### With IFC Enabled
The Custom Orchestrator tracks the pipeline's context. Once the `confidential` function executes, the pipeline's context is permanently upgraded to `confidential`. When the orchestrator attempts to pass that data to the `public` logging function, OPA intercepts the Traefik request and instantly returns `403 Forbidden`.

* **Allowed Pipeline (Upward Flow):** `public` → `internal` → `confidential`
* **Rejected Pipeline (Downward Leak):** `public` → `internal` → `confidential` → ❌ `public`

---

## Controlled Declassification

To safely lower a classification level (e.g., generating a public summary from confidential data), the system utilizes **Secure JSON Envelopes**. 

Functions wrap their outputs in metadata:
```json
{
    "ifc_metadata": { "classification": "confidential", "encrypted": true },
    "payload": "U2VjcmV0IEZpbmFuY2lhbCBEYXRh"
}