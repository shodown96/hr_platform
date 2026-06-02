# HR Platform — Microservice Architecture

## Overview

The HR platform is built as a collection of independent services, each responsible for its own slice of the business. They communicate through a combination of events (async) and direct API calls (sync), and none of them share a database.

The current platform consists of three services:

| Service | Port | Owns |
|---|---|---|
| **Auth Service** | 8001 | Users, roles, permissions, tokens |
| **Employee Service** | 8002 | Employees, departments, positions |
| **Payroll Service** | 8003 | Salaries, payroll records, payslips |

---

## Core Principles

**Each service owns its data.** No service ever reads directly from another service's database. If Employee Service needs to know something from Auth, it calls the Auth API or listens for an event.

**Events for state changes, REST for queries.** When something happens (employee terminated, salary changed), a message is published to the broker and any interested service reacts. When a service needs data right now (e.g. permission check), it makes a direct HTTP call.

**Failure tolerance.** If one service goes down, the others keep running. Events are queued and processed when the service comes back up. Permission checks fall back to the JWT token if the Auth Service is temporarily unreachable.

---

## How the Services Talk to Each Other

### Message Broker (RabbitMQ)

Events are published to named exchanges and consumed from named queues. Each service has its own queue so it never misses a message, even if it was temporarily offline.

```
Auth Service  ──publishes to──▶  "auth_events"     exchange
Employee Service  ──────────▶  "employee_events"  exchange
Payroll Service  ───────────▶  "payroll_events"   exchange
```

Every service subscribes to the exchanges it cares about with its own dedicated queue.

### Direct HTTP (httpx)

Used only when a real-time response is needed — primarily when a service has a cache miss and needs to fetch the current permissions for a user from the Auth Service.

---

## User Flows

### Hiring a New Employee

```
HR Admin creates a user account in Auth Service (POST /users/create-user)
        ↓
Auth Service creates the user, assigns default "employee" role
        ↓
Auth Service publishes: user.created
        ↓
HR Admin creates the employee record in Employee Service, linking it
to the user account via user_id (POST /employees)
        ↓
Employee Service publishes: employee.created
        ↓
Payroll Service receives event → creates salary placeholder
        ↓
(Future) Benefits Service receives event → enrols in benefits
```

---

### Employee Logs In

```
Employee submits username + password to Auth Service
        ↓
Auth Service verifies password (bcrypt)
        ↓
Auth Service loads roles and permissions from database
        ↓
JWT token is created with permissions embedded
        ↓
Token returned to employee
        ↓
Employee sends token with every subsequent request
        ↓
Each service validates token locally (no Auth Service call needed)
        ↓
Permissions checked against Redis cache (15-min TTL)
        ↓
If cache miss → fetch from Auth Service, cache the result
```

---

### Accessing a Protected Resource

```
Employee makes request to e.g. Employee Service
        ↓
Service extracts JWT from Authorization header
        ↓
Layer 1: Verify JWT signature + expiry (no DB call)
        ↓
Layer 2: Check Redis cache for this user's permissions
        ↓ (cache hit)                ↓ (cache miss)
Use cached permissions     Fetch from Auth Service via HTTP
                                      ↓
                           Cache the fresh permissions (15 min)
        ↓
Check: does this user have the required permission?
        ↓ yes                         ↓ no
  Request proceeds              403 Forbidden
```

---

### Updating an Employee's Role or Permissions

```
HR Admin assigns or removes a role via Auth Service
        ↓
Auth Service updates the database
        ↓
Auth Service publishes event: user.role.assigned / user.role.removed
        ↓
All services receive the event
        ↓
Each service clears that user's permission cache in Redis
        ↓
On their next request, the user gets fresh permissions fetched from Auth
        ↓
Change takes effect within seconds
```

> Caches are **invalidated** (cleared), never updated directly. This avoids race conditions and keeps things simple — the next request always fetches the truth from the source.

---

### Terminating an Employee

```
HR Admin triggers termination in Employee Service
        ↓
Employee Service sets employment_status = terminated
        ↓
Employee Service publishes: employee.terminated
        ↓
┌─────────────────────────────────────────────────────┐
│  Auth Service receives event                        │
│  → Sets user.is_active = false                      │
│  → Publishes: user.deactivated                      │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│  Payroll Service receives event                     │
│  → Deactivates salary record                        │
│  → Cancels future pending payrolls                  │
│  → Flags account for final pay calculation          │
└─────────────────────────────────────────────────────┘
        ↓
All services receive: user.deactivated
→ Clear that user's permission cache
→ Any active sessions are blocked on the next request
```

HR only needs to click "terminate" in one place. Everything else happens automatically.

---

### Changing an Employee's Salary

```
Payroll Admin creates a new salary record for the employee
        ↓
Payroll Service deactivates the old salary (sets effective_to date)
        ↓
Payroll Service creates the new active salary record
        ↓
Payroll Service publishes: salary.changed
        ↓
Finance Service receives event → updates budget forecasts
Audit Service receives event → logs change for compliance
```

---

### Running Payroll

```
Payroll Admin triggers payroll for a pay period
        ↓
Payroll Service calculates: gross salary + bonuses − deductions − taxes
        ↓
PayrollRecord created with status: pending
        ↓
Components added (basic pay, bonus, tax, etc.)
        ↓
Payroll marked as processed → status: paid
        ↓
Payroll Service publishes: payroll.processed
        ↓
Finance Service receives event → accounting integration
Banking Service receives event → initiates payment transfer
        ↓
Employee can download their payslip (PDF)
        ↓
If anything fails → status: failed
        ↓
Payroll Service publishes: payroll.failed
        ↓
Notification Service receives event → alerts HR and Finance
```

---

### Employee Changes Department or Position

```
HR Admin updates department or position in Employee Service
        ↓
Employee Service publishes:
  employee.department.changed  or  employee.position.changed
        ↓
┌──────────────────────────────────────────────────────┐
│  Auth Service receives event                         │
│  → If change is effective today or in the past:      │
│     Clear user's permission cache in Redis           │
│  → If change is future-dated:                        │
│     Log it — cache will be cleared on effective date │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│  Payroll Service receives event                      │
│  → Flags salary for review                           │
│  → New department/position may affect pay grade      │
└──────────────────────────────────────────────────────┘
```

---

### Password Reset

```
Employee submits their email address
        ↓
Auth Service generates a 6-digit OTP (expires in 10 minutes)
        ↓
OTP is sent to the employee's email
        ↓
Employee submits: email + OTP + new password
        ↓
Auth Service verifies OTP is correct and not expired
        ↓
Password updated, OTP deleted
        ↓
Employee logs in normally with new password
```

---

## Full Event Catalog

### Auth Service — Publishes

| Event | When | Who Reacts |
|---|---|---|
| `user.created` | New user account created | — |
| `user.role.assigned` | Role added to user | All services — clear permission cache |
| `user.role.removed` | Role removed from user | All services — clear permission cache |
| `user.permission.granted` | Permission directly granted to user | All services — clear permission cache |
| `user.permission.removed` | Permission directly revoked from user | All services — clear permission cache |
| `user.deactivated` | User account disabled | All services — block access, clear cache |
| `user.password.changed` | User changed their password | Audit |
| `user.password.reset` | User reset their password via OTP | Audit |

### Auth Service — Listens

| Event | From | Action Taken |
|---|---|---|
| `employee.created` | Employee Service | Link employee record to user |
| `employee.terminated` | Employee Service | Deactivate user account |
| `employee.updated` | Employee Service | Sync email if it changed |
| `employee.position.changed` | Employee Service | Clear permission cache |
| `employee.department.changed` | Employee Service | Clear permission cache |

---

### Employee Service — Publishes

| Event | When | Who Reacts |
|---|---|---|
| `employee.created` | New employee record added | Payroll: salary placeholder; Benefits: enrolment |
| `employee.updated` | Employee details changed | Auth: sync email |
| `employee.terminated` | Employee terminated | Auth: deactivate user; Payroll: stop salary |
| `employee.department.changed` | Department transfer | Auth: clear cache; Payroll: review salary |
| `employee.position.changed` | Promotion / demotion | Auth: clear cache; Payroll: salary adjustment |

### Employee Service — Listens

| Event | From | Action Taken |
|---|---|---|
| `user.role.assigned` | Auth Service | Clear permission cache for that user |
| `user.role.removed` | Auth Service | Clear permission cache for that user |
| `user.permission.granted` | Auth Service | Clear permission cache for that user |
| `user.deactivated` | Auth Service | Clear permission cache for that user |

---

### Payroll Service — Publishes

| Event | When | Who Reacts |
|---|---|---|
| `salary.created` | New salary set for employee | Finance: budget tracking; Reporting: compensation |
| `salary.changed` | Salary adjusted | Finance: update budget; Audit: compliance log |
| `payroll.processed` | Pay run completed | Finance: accounting; Banking: initiate payment |
| `payroll.failed` | Pay run failed | Notification: alert HR and Finance |

### Payroll Service — Listens

| Event | From | Action Taken |
|---|---|---|
| `employee.created` | Employee Service | Create salary placeholder |
| `employee.updated` | Employee Service | Update local employee copy |
| `employee.terminated` | Employee Service | Deactivate salary, cancel future payrolls |
| `employee.department.changed` | Employee Service | Flag salary for review |
| `employee.position.changed` | Employee Service | Flag salary for review |

---

## Roles & Permissions

Access control is role-based. Roles bundle permissions, users get roles, and effective access is the union of all permissions across all assigned roles.

### How permissions are checked (per request)

```
JWT token (signature + expiry check)
        ↓ valid
Redis cache lookup for this user's permissions
        ↓ miss
Fetch from Auth Service → cache for 15 minutes
        ↓
Permission check: does user have required permission?
```

### Default role on sign-up

Every new account is automatically assigned the `employee` role, which includes:
- `employee:read` — view their own profile
- `payroll:read` — view their own payroll records

---

## Account Lifecycle

```
Invited (account inactive)
    ↓ employee sets password
Active (can log in and use the platform)
    ↓ HR terminates employee
Deactivated (blocked immediately across all services)
```

Deactivation is instant — it doesn't wait for the JWT token to expire. The moment `user.deactivated` is published, every service clears the user's cache and any subsequent request is rejected.

---

## Deployment

| Environment | Approach |
|---|---|
| **Local development** | Docker Compose — all services + RabbitMQ + Redis + PostgreSQL |
| **Production (planned)** | Kubernetes — when scale requires auto-scaling and self-healing |

The path from Docker Compose to Kubernetes is intentionally straightforward. The same containers run in both environments; only the orchestration layer changes.

### Service URLs (local)

| Service | URL |
|---|---|
| Auth Service | http://localhost:8001/docs |
| Employee Service | http://localhost:8002/docs |
| Payroll Service | http://localhost:8003/docs |
| RabbitMQ UI | http://localhost:15672 |