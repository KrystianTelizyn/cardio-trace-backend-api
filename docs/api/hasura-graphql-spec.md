# Cardio Trace GraphQL Specification (Hasura)

GraphQL queries served by **Hasura**, proxied through the **cardio-trace-gateway** at `/graphql`. Hasura auto-generates queries, filters, sorting, and pagination from the PostgreSQL schema.

Write operations are handled by Django DRF — see [Backend API Specification](backend-api-spec.md).

Hasura permissions enforce **tenant isolation** and **role-based row/column access** using session variables forwarded by the gateway (`X-Hasura-Role`, `X-Hasura-Org-Id`, `X-Hasura-User-Id`). Hasura metadata and migrations live in the `cardio-trace-gateway` repository.

**Access legend:**

- `doctor` — authenticated user with doctor role
- `patient` — authenticated user with patient role

---

## Query Summary

| Query                  | Access          | Description                                      |
|------------------------|-----------------|--------------------------------------------------|
| patient_profiles       | doctor          | List patients in tenant (filter, paginate)       |
| patient_profiles_by_pk | doctor          | Single patient profile                           |
| measurements           | doctor, patient | Patient measurements (time-range filter)         |
| prescriptions          | doctor, patient | Prescriptions with nested drug                   |
| prescriptions_by_pk    | doctor, patient | Single prescription                              |
| dose_events            | doctor, patient | Dose events (filter by prescription, time-range) |
| alerts                 | doctor, patient | Alerts with nested alert_type                    |
| devices                | doctor          | List devices in tenant                           |
| devices_by_pk          | doctor          | Single device                                    |
| device_assignments     | doctor          | Current device-to-patient mappings               |
| drugs                  | doctor, patient | Drug reference catalog                           |
| alert_types            | doctor, patient | Alert type reference catalog                     |
| doctor_profiles        | doctor, patient | List doctors in tenant                           |
| doctor_profiles_by_pk  | doctor, patient | Single doctor profile                            |

---

## Permission Model

Row-level access per role. Tenant isolation is enforced on every table that carries `tenant_id`. Patient-scoped tables additionally restrict patients to their own rows.

| Table              | doctor                     | patient                    |
|--------------------|----------------------------|----------------------------|
| patient_profiles   | all in own tenant          | own profile only           |
| doctor_profiles    | all in own tenant          | all in own tenant          |
| measurements       | all patients in own tenant | own measurements only      |
| prescriptions      | all patients in own tenant | own prescriptions only     |
| dose_events        | all patients in own tenant | own dose events only       |
| alerts             | all patients in own tenant | own alerts only            |
| devices            | all in own tenant          | —                          |
| device_assignments | all in own tenant          | —                          |
| drugs              | all (global)               | all (global)               |
| alert_types        | all (global)               | all (global)               |

---

## Relationship Traversals

Hasura exposes nested relationships automatically. The SPA can query across these in a single GraphQL request:

- `patient_profiles` → `measurements`, `prescriptions`, `alerts`, `dose_events`, `device_assignments`
- `prescriptions` → `drug` (object), `doctor_profile` (object), `dose_events` (array)
- `alerts` → `alert_type` (object), `device` (object)
- `device_assignments` → `device` (object), `patient_profile` (object)
- `measurements` → `device` (object)

---

## Data Shapes

### PatientProfile

| Field      | Type   | Description         |
|------------|--------|---------------------|
| id         | int    |                     |
| name       | string |                     |
| dob        | date   | Date of birth       |
| gender     | string |                     |
| medical_id | string | External medical ID |

### DoctorProfile

| Field          | Type   | Description |
|----------------|--------|-------------|
| id             | int    |             |
| name           | string |             |
| specialization | string |             |
| license_number | string |             |

### Measurement

| Field      | Type     | Description                 |
|------------|----------|-----------------------------|
| id         | int      |                             |
| device_id  | int      | Source device               |
| device     | object   | Nested Device               |
| patient_id | int      |                             |
| timestamp  | datetime | When the reading was taken  |
| heart_rate | float    | Beats per minute            |
| hrv        | float    | Heart rate variability (ms) |

### Prescription

| Field          | Type   | Description                       |
|----------------|--------|-----------------------------------|
| id             | int    |                                   |
| patient_id     | int    |                                   |
| doctor_id      | int    |                                   |
| doctor_profile | object | Nested DoctorProfile              |
| drug_id        | int    |                                   |
| drug           | object | Nested Drug (id, name, producent) |
| date_assigned  | date   |                                   |
| dosage         | string |                                   |
| frequency      | string |                                   |
| start_date     | date   |                                   |
| end_date       | date   | Null if ongoing                   |

### DoseEvent

| Field           | Type     | Description              |
|-----------------|----------|--------------------------|
| id              | int      |                          |
| prescription_id | int      |                          |
| prescription    | object   | Nested Prescription      |
| patient_id      | int      |                          |
| timestamp       | datetime | When the dose was taken  |

### Alert

| Field         | Type     | Description                     |
|---------------|----------|---------------------------------|
| id            | int      |                                 |
| patient_id    | int      |                                 |
| device_id     | int      |                                 |
| device        | object   | Nested Device                   |
| alert_type_id | int      |                                 |
| alert_type    | object   | Nested AlertType (id, name)     |
| message       | string   |                                 |
| timestamp     | datetime | When the alert was raised       |

### Device

| Field         | Type   | Description  |
|---------------|--------|--------------|
| id            | int    |              |
| serial_number | string |              |
| brand         | string |              |
| name          | string | Device model |

### DeviceAssignment

| Field           | Type   | Description           |
|-----------------|--------|-----------------------|
| id              | int    |                       |
| device_id       | int    |                       |
| device          | object | Nested Device         |
| patient_id      | int    |                       |
| patient_profile | object | Nested PatientProfile |

### Drug

| Field     | Type   | Description  |
|-----------|--------|--------------|
| id        | int    |              |
| name      | string |              |
| producent | string | Manufacturer |

### AlertType

| Field       | Type   | Description |
|-------------|--------|-------------|
| id          | int    |             |
| name        | string |             |
| description | string |             |
