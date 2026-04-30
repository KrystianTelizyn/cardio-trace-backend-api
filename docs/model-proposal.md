# Data Model

## Tenants

* id (PK)
* name
* auth0_organization_id (unique)

## Users (Custom User)

* id (PK)
* auth0_user_id (unique)
* email
* tenant_id (FK → Tenants)
* date_joined
* last_login

## PatientProfiles

* id (PK)
* user_id (FK → Users, unique)
* tenant_id (FK → Tenants)
* name
* dob
* gender
* medical_id

## DoctorProfiles

* id (PK)
* user_id (FK → Users, unique)
* tenant_id (FK → Tenants)
* name
* specialization
* license_number

## Devices

* id (PK)
* serial_number (unique)
* brand
* name
* tenant_id (FK → Tenants)

## DeviceAssignments

* id (PK)
* tenant_id (FK → Tenants)
* device_id (FK → Devices)
* patient_id (FK → PatientProfiles)
* doctor_id (FK → DoctorProfiles)
* assigned_at
* unassigned_at (nullable while active)
* created_at
* updated_at

Represents a device assignment lifecycle row. The assignment is active while `unassigned_at` is null and becomes historical when `unassigned_at` is set. Constraints enforce one active assignment per device per tenant and one active assignment per patient per tenant.

## MeasurementSessions

* id (PK, ULID)
* tenant_id (FK → Tenants)
* device_assignment_id (FK → DeviceAssignments)
* started_at
* stopped_at (nullable while active)
* status (`active`, `stopped`)
* created_at
* updated_at

Represents the patient-confirmed period when the assigned HR monitor is actually being worn. Device, patient, and doctor ownership are derived through `device_assignment_id`. A patient starts and stops sessions from the frontend app. The ingestion service resolves incoming device data to the active session and sends that session identifier to the backend API with each measurement frame.

## Measurements

* id (PK, UUID)
* tenant_id (FK → Tenants)
* measurement_session_id (FK → MeasurementSessions)
* timestamp
* heart_rate
* hrv

Device, patient, and assignment ownership are derived through `measurement_session_id`.

## Drugs

* id (PK)
* name
* producent

## Prescriptions

* id (PK)
* patient_id (FK → PatientProfiles)
* doctor_id (FK → DoctorProfiles)
* drug_id (FK → Drugs)
* tenant_id (FK → Tenants)
* date_assigned
* dosage
* frequency
* start_date
* end_date

## DoseEvents

* id (PK)
* prescription_id (FK → Prescriptions)
* patient_id (FK → PatientProfiles)
* tenant_id (FK → Tenants)
* timestamp

## Alerts

* id (PK)
* patient_id (FK → PatientProfiles)
* tenant_id (FK → Tenants)
* device_id (FK → Devices)
* alert_type_id (FK → AlertTypes)
* message
* timestamp

## AlertTypes

* id (PK)
* name
* description

## EventLog

* id (PK)
* event
* time
* payload
