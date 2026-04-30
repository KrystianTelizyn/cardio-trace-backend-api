# Cardio Trace Core Backend API Specification

REST API served by **Django DRF** (`cardio-trace-backend-api`). All endpoints are reached through the **cardio-trace-gateway** proxy (`/api/*`). Tenant scoping is implicit — derived from gateway-forwarded internal headers (`X-Tenant-Id`, `X-User-Id`, `X-Role`). No endpoint requires a tenant ID in the URL or body (except internal endpoints where noted).

Internal ingestion endpoints are called directly by platform services (sensor-hub, workers), not through the gateway.

Data reads are served by Hasura — see [GraphQL Specification](hasura-graphql-spec.md).

**Access legend:**

- `doctor` — authenticated user with doctor role
- `patient` — authenticated user with patient role
- `internal` — called by platform services, not browser traffic

---

## Endpoint Summary

| Method | Path                              | Access             | Description                                  |
|--------|-----------------------------------|--------------------|----------------------------------------------|
| POST   | /users                            | internal           | Provision user + profile on first login      |
| PATCH  | /me/profile                       | doctor, patient    | Update own profile (post-registration etc.)  |
| POST   | /ingestion/enrich                 | internal           | Resolve device/session context for ingestion |
| POST   | /measurements                     | internal           | Ingest measurement for resolved session      |
| POST   | /measurement-sessions             | patient            | Start a measurement session                  |
| PATCH  | /measurement-sessions/{id}        | patient            | Stop a measurement session                   |
| POST   | /patients/{id}/prescriptions      | doctor             | Create a prescription                        |
| PATCH  | /prescriptions/{id}               | doctor             | Update a prescription                        |
| POST   | /me/dose-events                   | patient            | Record a dose event                          |
| POST   | /alerts                           | internal           | Create alert from workers pipeline           |
| PATCH  | /alerts/{id}                      | doctor             | Acknowledge or dismiss an alert              |
| POST   | /devices                          | doctor             | Register a new device                        |
| POST   | /device-assignments               | doctor             | Assign a device to a patient                 |
| PATCH  | /device-assignments/{id}          | doctor             | Stop an active device assignment             |

---

## Detailed Specifications

### User Provisioning

#### POST /users

Provision a new user and their domain profile. Called by the gateway during the first-login-from-invite callback flow. Idempotent — if a user with the given `auth0_user_id` already exists, returns the existing record.

**Access:** `internal`

**Request body:**

| Field         | Type   | Required | Description                                |
|---------------|--------|----------|--------------------------------------------|
| auth0_user_id | string | yes      | `sub` from Auth0 token                     |
| auth0_org_id  | string | yes      | `org_id` from Auth0 token                  |
| role          | string | yes      | `doctor` or `patient`                      |
| email         | string | yes      | From Auth0 userinfo                        |
| name          | string | no       | From Auth0 userinfo                        |

Backend resolves `auth0_org_id` → local Tenant, creates User, and creates a PatientProfile or DoctorProfile based on `role`, seeded with `name`. Domain-specific fields (specialization, license_number, dob, medical_id) start as null.

**Response 201** (created) / **200** (already exists):

| Field         | Type   | Description                                 |
|---------------|--------|---------------------------------------------|
| id            | int    | User ID                                     |
| auth0_user_id | string |                                             |
| email         | string |                                             |
| role          | string | `doctor` or `patient`                       |
| profile       | object | DoctorProfile or PatientProfile (see below) |

**PatientProfile shape:**

| Field      | Type   | Description         |
|------------|--------|---------------------|
| id         | int    |                     |
| name       | string |                     |
| surname    | string |                     |
| dob        | date   | Date of birth       |
| gender     | string |                     |
| medical_id | string | External medical ID |

**DoctorProfile shape:**

| Field          | Type   | Description |
|----------------|--------|-------------|
| id             | int    |             |
| name           | string |             |
| surname        | string |             |
| specialization | string |             |
| license_number | string |             |

**Errors:** `400` — validation error, `404` — tenant not found for given `auth0_org_id`

---

### Profile Update

#### PATCH /me/profile

Update the authenticated user's own profile. Intended for post-registration completion (e.g. doctor fills in `license_number`, patient fills in `medical_id`) and ongoing profile edits. The backend determines whether to update a DoctorProfile or PatientProfile based on the authenticated user's role.

**Access:** `doctor`, `patient`

**Request body (partial update — all fields optional, send only what changes):**

*Doctor fields:*

| Field          | Type   | Required | Description                    |
|----------------|--------|----------|--------------------------------|
| name           | string | no       | First name                     |
| surname        | string | no       | Last name                      |
| specialization | string | no       | Medical specialization         |
| license_number | string | no       | Professional license number    |

*Patient fields:*

| Field      | Type   | Required | Description         |
|------------|--------|----------|---------------------|
| name       | string | no       | First name          |
| surname    | string | no       | Last name           |
| dob        | date   | no       | Date of birth       |
| gender     | string | no       | Gender              |
| medical_id | string | no       | External medical ID |

Fields that do not belong to the user's role are silently ignored.

**Response 200:** Updated profile object (DoctorProfile or PatientProfile shape, same as in User Provisioning above).

**Errors:** `400` — validation error

---

### Measurements

#### POST /ingestion/enrich

Resolve external device identity into ingestion-ready internal context in one call. This endpoint is intended for high-frequency internal telemetry pipelines before `POST /measurements`.

**Access:** `internal`

**Request body:**

| Field         | Type   | Required | Description                                  |
|---------------|--------|----------|----------------------------------------------|
| serial_number | string | yes      | Device serial number                         |
| brand         | string | yes      | Device brand                                 |

**Response 200:**

| Field      | Type        | Description                                                  |
|------------|-------------|--------------------------------------------------------------|
| device_uid | string      | Stable internal device identifier (8 chars, lowercase alphanumeric) |
| session_uid| ulid-string | Active measurement session identifier, or `null` if missing |

**Errors:** `400` — validation error, `404` — device identity not found

---

#### POST /measurements

Ingest a measurement from the sensor-hub pipeline. The ingestion service is responsible for device identification and active session resolution. It sends the resolved `measurement_session_id` with the reading data, and the backend API validates the session before storing the frame.

**Access:** `internal`

**Request body:**

| Field                  | Type     | Required | Description                       |
|------------------------|----------|----------|-----------------------------------|
| measurement_session_id | ulid     | yes      | Active session resolved upstream  |
| timestamp              | datetime | yes      | Reading timestamp                 |
| heart_rate             | float    | yes      | BPM                               |
| hrv                    | float    | yes      | Heart rate variability (ms)       |

**Response 201:** Created Measurement object

| Field                  | Type     | Description                             |
|------------------------|----------|-----------------------------------------|
| id                     | uuid     | Measurement identifier                  |
| measurement_session_id | ulid     | Session provided by ingestion service   |
| timestamp              | datetime |                                         |
| heart_rate             | float    |                                         |
| hrv                    | float    |                                         |

**Errors:** `400` — validation error, `404` — measurement session not found, `202` — measurement frame dropped because measurement session is stopped (`measurement_dropped_session_stopped`)

---

### Measurement Sessions

Measurement sessions represent the period when a patient explicitly starts wearing an assigned HR monitor. Patients discover available assignments and existing sessions through GraphQL reads, then use these write endpoints to start or stop the session lifecycle.

#### POST /measurement-sessions

Start a new measurement session for the authenticated patient and an active device assignment.

**Access:** `patient`

**Request body:**

| Field                | Type     | Required | Description                                            |
|----------------------|----------|----------|--------------------------------------------------------|
| device_assignment_id | int      | yes      | Assignment being used for this session                 |
| started_at           | datetime | no       | Defaults to server time if omitted                     |

The backend validates that the assignment belongs to the current tenant and is active at session start (`unassigned_at IS NULL`). Only one active MeasurementSession is allowed per assignment.

**Response 201:** Created MeasurementSession object

| Field                | Type     | Description                         |
|----------------------|----------|-------------------------------------|
| id                   | ulid     | MeasurementSession identifier       |
| started_at           | datetime | When the patient started the session |
| status               | string   | `active`                            |

**Errors:** `400` — validation error or `started_at` outside assignment window, `404` — assignment not found in tenant, `409` — active session already exists for the assignment

---

#### PATCH /measurement-sessions/{id}

Stop an active measurement session.

**Access:** `patient`

**Parameters:**

| Param | In   | Type | Required | Description            |
|-------|------|------|----------|------------------------|
| id    | path | ulid | yes      | MeasurementSession ID  |

**Request body:**

| Field      | Type     | Required | Description                        |
|------------|----------|----------|------------------------------------|
| stopped_at | datetime | no       | Defaults to server time if omitted |

The backend resolves the session by `id` within the current tenant. `stopped_at` must be after `started_at`. If the session is already stopped, the endpoint returns the existing stopped session state (idempotent success).

**Response 200:** Updated MeasurementSession object

| Field                | Type     | Description                         |
|----------------------|----------|-------------------------------------|
| id                   | ulid     | MeasurementSession identifier       |
| started_at           | datetime |                                     |
| stopped_at           | datetime | When the patient stopped the session |
| status               | string   | `stopped`                           |

**Errors:** `400` — validation error or invalid stop time, `404` — session not found in tenant

---

### Prescriptions

#### POST /patients/{id}/prescriptions

Create a new prescription for a patient.

**Access:** `doctor`

**Parameters:**

| Param | In   | Type | Required | Description |
|-------|------|------|----------|-------------|
| id    | path | int  | yes      | Patient ID  |

**Request body:**

| Field      | Type   | Required | Description         |
|------------|--------|----------|---------------------|
| drug_id    | int    | yes      | Reference to Drugs  |
| dosage     | string | yes      | e.g. "50mg"        |
| frequency  | string | yes      | e.g. "twice daily" |
| start_date | date   | yes      |                     |
| end_date   | date   | no       | Null if ongoing     |

`doctor_id` and `date_assigned` are set automatically from the authenticated user context.

**Response 201:** Created Prescription object

| Field         | Type   | Description                       |
|---------------|--------|-----------------------------------|
| id            | int    |                                   |
| patient_id    | int    |                                   |
| doctor_id     | int    | Prescribing doctor                |
| drug          | object | Nested Drug (id, name, producent) |
| date_assigned | date   | When the prescription was written |
| dosage        | string |                                   |
| frequency     | string |                                   |
| start_date    | date   |                                   |
| end_date      | date   | Null if ongoing                   |

**Errors:** `400` — validation error, `404` — patient or drug not found

---

#### PATCH /prescriptions/{id}

Update a prescription (e.g. change end_date to discontinue).

**Access:** `doctor`

**Parameters:**

| Param | In   | Type | Required | Description     |
|-------|------|------|----------|-----------------|
| id    | path | int  | yes      | Prescription ID |

**Request body (partial update):**

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| dosage    | string | no       |             |
| frequency | string | no       |             |
| end_date  | date   | no       |             |

**Response 200:** Updated Prescription object

**Errors:** `400` — validation error, `404` — not found or not in current tenant

---

### Dose Events

#### POST /me/dose-events

Record a dose event (patient confirms they took medication).

**Access:** `patient`

**Request body:**

| Field           | Type     | Required | Description                    |
|-----------------|----------|----------|--------------------------------|
| prescription_id | int      | yes      | Which prescription this is for |
| timestamp       | datetime | no       | Defaults to now if omitted     |

**Response 201:**

| Field           | Type     | Description             |
|-----------------|----------|-------------------------|
| id              | int      |                         |
| prescription_id | int      | Parent prescription     |
| timestamp       | datetime | When the dose was taken |

**Errors:** `400` — validation error, `404` — prescription not found or not owned by patient

---

### Alerts

#### POST /alerts

Create an alert from the workers pipeline.

**Access:** `internal`

**Request body:**

| Field         | Type     | Required | Description                     |
|---------------|----------|----------|---------------------------------|
| patient_id    | int      | yes      |                                 |
| device_id     | int      | yes      | Device that triggered the alert |
| tenant_id     | int      | yes      | Tenant scope                    |
| alert_type_id | int      | yes      | Reference to AlertTypes         |
| message       | string   | yes      | Human-readable detail           |
| timestamp     | datetime | yes      | When the condition was detected |

**Response 201:** Created Alert object

| Field      | Type     | Description                     |
|------------|----------|---------------------------------|
| id         | int      |                                 |
| patient_id | int      |                                 |
| device_id  | int      | Device that triggered the alert |
| alert_type | object   | Nested AlertType (id, name)     |
| message    | string   |                                 |
| timestamp  | datetime |                                 |

**Errors:** `400` — validation error

---

#### PATCH /alerts/{id}

Acknowledge or dismiss an alert.

**Access:** `doctor`

**Parameters:**

| Param | In   | Type | Required | Description |
|-------|------|------|----------|-------------|
| id    | path | int  | yes      | Alert ID    |

**Request body:**

| Field        | Type   | Required | Description                |
|--------------|--------|----------|----------------------------|
| acknowledged | bool   | no       | Mark as acknowledged       |
| note         | string | no       | Doctor's note on the alert |

**Response 200:** Updated Alert object

**Errors:** `404` — not found or not in current tenant

---

### Devices

#### POST /devices

Register a new device.

**Access:** `doctor`

**Request body:**

| Field         | Type   | Required | Description    |
|---------------|--------|----------|----------------|
| serial_number | string | yes      | Must be unique |
| brand         | string | yes      |                |
| name          | string | yes      | Device model   |

**Response 201:**

| Field         | Type   | Description |
|---------------|--------|-------------|
| id            | int    |             |
| serial_number | string |             |
| brand         | string |             |
| name          | string |             |

**Errors:** `400` — validation error (e.g. duplicate serial_number)

---

### Device Assignments

#### POST /device-assignments

Create an active device assignment for a patient.

**Access:** `doctor`

**Request body:**

| Field      | Type | Required | Description |
|------------|------|----------|-------------|
| device_id  | int  | yes      |             |
| patient_id | int  | yes      |             |

**Response 201:**

| Field         | Type     | Description                            |
|---------------|----------|----------------------------------------|
| id            | int      |                                        |
| device_id     | int      |                                        |
| patient_id    | int      |                                        |
| doctor_id     | int      | Assigning doctor                       |
| assigned_at   | datetime | When assignment became active          |
| unassigned_at | datetime | Null while active; set when stopped    |

An assignment is active while `unassigned_at` is null. The backend enforces one active assignment per device per tenant and one active assignment per patient per tenant.

**Errors:** `400` — validation error, `404` — device or patient not found, `409` — device already actively assigned or patient already has an active assignment

---

#### PATCH /device-assignments/{id}

Stop an active device assignment by setting `unassigned_at`.

**Access:** `doctor`

**Parameters:**

| Param | In   | Type | Required | Description   |
|-------|------|------|----------|---------------|
| id    | path | int  | yes      | Assignment ID |

**Request body (optional):**

| Field         | Type     | Required | Description                                 |
|---------------|----------|----------|---------------------------------------------|
| unassigned_at | datetime | no       | Defaults to server time if omitted          |

**Response 200:** Updated DeviceAssignment object

| Field         | Type     | Description                            |
|---------------|----------|----------------------------------------|
| id            | int      |                                        |
| device_id     | int      |                                        |
| patient_id    | int      |                                        |
| doctor_id     | int      |                                        |
| assigned_at   | datetime |                                        |
| unassigned_at | datetime | Stop timestamp                         |

**Errors:** `404` — not found or not in current tenant, `409` — assignment already stopped
