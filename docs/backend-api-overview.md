# cardio-trace-backend-api

Core domain service for the Cardio Trace Platform. Django REST Framework application backed by PostgreSQL.

## Role in the Platform

This service owns **domain data and business logic** — patients, doctors, devices, measurements, prescriptions, alerts. It does **not** handle authentication, login flows, or session management; those belong to the [gateway](https://github.com/KrystianTelizyn/cardio-trace-gateway).

For the full platform architecture, see the [platform README](../README.md).

### What this service does

- **Stores and manages all domain data** in PostgreSQL (the single source of truth for the platform's relational data)
- **Serves write endpoints** — updating profiles, creating prescriptions, recording dose events, registering devices, acknowledging alerts
- **Accepts internal ingestion** — measurements from sensor-hub, alerts from workers, user provisioning from gateway
- **Enforces domain authorization** — tenant isolation, ownership checks, business rules (e.g. one active assignment per device and per patient in tenant scope)

### What this service does NOT do

- **Serve data reads to the SPA** — Hasura handles all read queries via GraphQL ([ADR 0014](adr/0014-hasura-reads-drf-writes.md))
- **Authenticate users or validate JWTs** — the gateway does this and forwards trusted headers ([ADR 0004](adr/0004-backend-auth-separation.md), [ADR 0012](adr/0012-gateway-backend-trust-contract.md))
- **Manage Auth0 flows** — login, callback, invites, role assignment belong to the gateway ([ADR 0002](adr/0002-idp-auth0.md))
- **Store passwords or role tables** — Auth0 owns credentials and RBAC ([ADR 0002](adr/0002-idp-auth0.md), [ADR 0006](adr/0006-role-permission-model.md))

## Key Architecture Decisions

Read these ADRs before implementing:

| ADR | Relevance to backend |
|-----|----------------------|
| [0004 — Gateway/Backend separation](adr/0004-backend-auth-separation.md) | Defines what the backend owns vs. what the gateway owns |
| [0005 — Multi-tenancy](adr/0005-mulit-tenancy.md) | Tenant isolation via `org_id` mapped to local Tenant records |
| [0006 — Role & permission model](adr/0006-role-permission-model.md) | No local role tables; roles come from gateway headers |
| [0012 — Internal trust contract](adr/0012-gateway-backend-trust-contract.md) | Exact headers the backend reads: `X-User-Id`, `X-Tenant-Id`, `X-Role` |
| [0013 — User provisioning](adr/0013-user-provisioning-first-login.md) | How users get created: gateway calls `POST /users` on first login |
| [0014 — Read/write split](adr/0014-hasura-reads-drf-writes.md) | Backend serves writes only; Hasura serves all SPA reads |

## Tech Stack

- **Python 3.12+**
- **Django** + **Django REST Framework**
- **PostgreSQL** (shared with Hasura for reads)
- No JWT/Auth0 libraries needed — the backend trusts gateway-forwarded headers

## Data Model

Full model with PK/FK relationships: [Data Model](../Model%20Proposal.md)

Key entities: Tenants, Users, PatientProfiles, DoctorProfiles, Devices, DeviceAssignments, MeasurementSessions, Measurements, Drugs, Prescriptions, DoseEvents, Alerts, AlertTypes, EventLog.

Measurements are session-based: `Measurement` records are linked to `MeasurementSession`, and patient/device ownership is derived through the related device assignment.

The User model is a **custom Django user** (`AbstractBaseUser` or similar) with `auth0_user_id` as the identity link — no password field.

## API Specification

Full endpoint details with request/response shapes: [Backend API Spec](api/backend-api-spec.md)

Summary of endpoints:

| Method | Path                              | Access          | Description                              |
|--------|-----------------------------------|-----------------|------------------------------------------|
| POST   | /users                            | internal        | Provision user + profile on first login  |
| PATCH  | /me/profile                       | doctor, patient | Update own profile (post-registration)   |
| POST   | /ingestion/enrich                 | internal        | Resolve device/session context upstream  |
| POST   | /measurements                     | internal        | Ingest measurement for resolved session  |
| POST   | /measurement-sessions             | patient         | Start a measurement session              |
| PATCH  | /measurement-sessions/{id}        | patient         | Stop a measurement session               |
| POST   | /patients/{id}/prescriptions      | doctor          | Create a prescription                    |
| PATCH  | /prescriptions/{id}               | doctor          | Update a prescription                    |
| POST   | /me/dose-events                   | patient         | Record a dose event                      |
| POST   | /alerts                           | internal        | Create alert from workers                |
| PATCH  | /alerts/{id}                      | doctor          | Acknowledge or dismiss an alert          |
| POST   | /devices                          | doctor          | Register a new device                    |
| POST   | /device-assignments               | doctor          | Assign a device to a patient             |
| PATCH  | /device-assignments/{id}          | doctor          | Stop an active device assignment         |

## Callers

| Caller | Endpoints used | Auth mechanism |
|--------|---------------|----------------|
| **SPA** (via gateway) | All `doctor`/`patient` endpoints | Gateway-forwarded headers ([ADR 0012](adr/0012-gateway-backend-trust-contract.md)) |
| **Gateway** | `POST /users` | Internal network (Docker) |
| **Sensor-hub** | `POST /ingestion/enrich`, `POST /measurements` | Internal network (Docker) |
| **Workers** | `POST /alerts` | Internal network (Docker) |

## Implementation Notes

### Authentication middleware

Build a custom DRF authentication class that:
1. Reads `X-User-Id`, `X-Tenant-Id`, `X-Role` from request headers
2. Resolves `X-User-Id` to a local User instance
3. Attaches `request.user` and `request.tenant` to the DRF request
4. Returns 401 if headers are missing (browser traffic) or user not found

Internal endpoints (sensor-hub, workers) use internal authentication and carry trusted entity identifiers in the request body.

### Tenant isolation

Every queryset for tenant-scoped models must filter by `tenant_id = request.tenant.id`. Consider a base viewset mixin or custom manager that applies this automatically.

### Database

PostgreSQL is shared between this service (Django ORM for writes) and Hasura (direct read access). Django manages the schema via migrations. Hasura tracks the same tables for GraphQL reads — its metadata lives in the [gateway repo](https://github.com/KrystianTelizyn/cardio-trace-gateway).
