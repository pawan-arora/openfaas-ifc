# OpenFaaS IFC

Information Flow Control (IFC) enforcement framework for OpenFaaS using Keycloak, Traefik, OPA, and a custom pipeline orchestrator.

## Overview

This project explores how Information Flow Control (IFC) can be integrated into OpenFaaS to prevent unsafe information flows between serverless functions.

Traditional OpenFaaS security focuses on authentication and access control. This project extends the model by introducing:

- Security labels for functions
- User clearance levels embedded in JWT tokens
- Flow validation across function pipelines
- Controlled declassification support

The goal is to prevent accidental data leaks when composing FaaS functions.

---

## Architecture

The system integrates:

- **Keycloak** – Adds `ifc_clearance` to JWT tokens
- **Traefik** – Handles authentication and routing
- **OPA (Open Policy Agent)** – Enforces IFC policy at function level
- **Custom Orchestrator** – Enforces IFC across pipelines

High-level flow:

User → Traefik → OPA → OpenFaaS Function  
Pipeline → Orchestrator → Multiple Functions (with IFC enforcement)

---

## Security Model

Three security levels are defined:

- `public`
- `internal`
- `confidential`

Rules enforced:

- A user can only invoke functions at or below their clearance.
- Pipelines are rejected if they would cause information to flow from higher to lower sensitivity without explicit declassification.
- Declassification must be controlled and explicit.

---

## Example Scenario

### Without IFC
A confidential function could accidentally send sensitive data to a public function.

### With IFC Enabled
The system rejects such pipelines automatically.

Example rejected pipeline:

public → internal → confidential → public

Example allowed pipeline:

public → internal → confidential

Example controlled declassification:

confidential → aggregate-report → public

---

## Controlled Declassification

Certain functions (e.g., aggregation functions) are permitted to safely downgrade classification after transforming sensitive data into non-sensitive summaries.

This demonstrates practical IFC enforcement in serverless environments.

---

## Evaluation

The system is evaluated by comparing:

- IFC disabled vs IFC enabled
- Authorized vs unauthorized users
- Valid vs invalid pipelines
- Controlled declassification behavior

---

## Running the System

1. Deploy Keycloak realm with `ifc_clearance`
2. Apply Traefik JWT middleware
3. Deploy OPA with `ifc_enforce.rego`
4. Deploy labelled OpenFaaS functions
5. Run the orchestrator
6. Test using provided example pipelines

---

## Research Context

This prototype demonstrates that Information Flow Control can be practically integrated into serverless platforms like OpenFaaS, extending beyond traditional access control to protect against unintended data flows in composed function pipelines.

---

## License

Research prototype – Academic use.
