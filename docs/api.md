# API Reference

Tài liệu này mô tả contract HTTP/WebSocket chính của Smart Study Room backend và AI service. Backend REST API chạy mặc định tại `http://localhost:8080`; AI service chạy mặc định tại `http://localhost:8000`.

## 1. Backend REST Conventions

### Base URL

```text
http://localhost:8080
```

### Response Envelope

Backend responses are wrapped in `ApiResponse<T>`:

```json
{
  "code": 0,
  "message": "success",
  "timestamp": "2026-06-06T10:30:00",
  "result": {}
}
```

For endpoints that do not return a domain object, `result` may be omitted or null.

### Error Envelope

Errors use the same envelope shape with non-zero `code` and an error `message`:

```json
{
  "code": 4000,
  "message": "Device not found",
  "timestamp": "2026-06-06T10:30:00"
}
```

### Authentication

Authenticated endpoints require:

```http
Authorization: Bearer <jwt-token>
```

Public backend endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/verify`
- `POST /auth/refresh`
- `POST /iot/sensor-data`
- `POST /sensor-data`
- `POST /sensors/sensor-data`
- `/ws/**`

Most user-scoped endpoints require either:

- The authenticated user id equals `{userId}`.
- The authenticated user has admin authority.

## 2. Domain Enums

| Enum | Values |
|---|---|
| `SensorType` | `TEMPERATURE`, `LIGHT`, `HUMIDITY` |
| `DeviceType` | `FAN`, `LIGHT` |
| `CommandType` | `AUTO_RULE`, `SPEECH`, `MANUAL` |
| `Operator` | `EQ`, `NEQ`, `LT`, `GT`, `LE`, `GE` |
| `Role` | `USER`, `ADMIN` |

## 3. Auth API

### Register

```http
POST /auth/register
Content-Type: application/json
```

Request:

```json
{
  "email": "student@example.com",
  "phone": "0900000000",
  "password": "password123",
  "firstName": "Bui",
  "middleName": "Nhat",
  "lastName": "Qui"
}
```

Response result:

```json
{
  "id": "user-id",
  "email": "student@example.com",
  "phone": "0900000000",
  "firstName": "Bui",
  "middleName": "Nhat",
  "lastName": "Qui",
  "fullName": "Bui Nhat Qui",
  "roles": ["USER"]
}
```

### Login

```http
POST /auth/login
Content-Type: application/json
```

Request:

```json
{
  "identifier": "student@example.com",
  "password": "password123"
}
```

Response result:

```json
{
  "token": "<jwt-token>"
}
```

### Logout

```http
POST /auth/logout
Content-Type: application/json
```

Request:

```json
{
  "token": "<jwt-token>"
}
```

### Verify Token

```http
POST /auth/verify
Content-Type: application/json
```

Request:

```json
{
  "token": "<jwt-token>"
}
```

Response result:

```json
{
  "valid": true
}
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json
```

Request:

```json
{
  "token": "<jwt-token>"
}
```

Response result:

```json
{
  "token": "<new-jwt-token>"
}
```

## 4. Users API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users` | JWT | List users |
| `GET` | `/users/{userId}` | JWT | Get user by id |
| `GET` | `/users/my-info` | JWT | Get authenticated user |
| `PUT` | `/users/{userId}` | JWT | Update user profile |
| `DELETE` | `/users/{userId}` | JWT | Delete user |

Update request:

```json
{
  "email": "student@example.com",
  "phone": "0900000000",
  "password": "new-password",
  "firstName": "Bui",
  "middleName": "Nhat",
  "lastName": "Qui"
}
```

User response result:

```json
{
  "id": "user-id",
  "email": "student@example.com",
  "phone": "0900000000",
  "firstName": "Bui",
  "middleName": "Nhat",
  "lastName": "Qui",
  "fullName": "Bui Nhat Qui",
  "createdAt": "2026-06-06T10:30:00",
  "lastUpdated": "2026-06-06T10:30:00",
  "lastLogin": "2026-06-06T10:30:00",
  "roles": ["USER"]
}
```

## 5. Sensors API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{userId}/sensors` | JWT | List sensors for a user |
| `GET` | `/users/{userId}/sensors/{sensorId}` | JWT | Get sensor detail |
| `GET` | `/users/{userId}/sensors/{sensorId}/data` | JWT | Get sensor history |
| `DELETE` | `/users/{userId}/sensors/{sensorId}/data` | JWT | Delete sensor history, optional date range |

Sensor response result:

```json
{
  "id": "sensor-id",
  "sensorType": "TEMPERATURE",
  "currentValue": 28.5
}
```

Sensor data response item:

```json
{
  "timestamp": "2026-06-06T10:30:00",
  "value": 28.5
}
```

Delete sensor data query params:

```http
DELETE /users/{userId}/sensors/{sensorId}/data?from=2026-06-06T00:00:00&to=2026-06-06T23:59:59
```

Response result is an integer count of deleted rows.

## 6. IoT Sensor Ingest API

These endpoints are aliases handled by the same controller:

```http
POST /iot/sensor-data
POST /sensor-data
POST /sensors/sensor-data
```

Request:

```json
{
  "userId": "c7ab5c64-cee4-4ef6-9b2e-1f71824c0920",
  "sensorType": "TEMPERATURE",
  "value": 28.5
}
```

Notes:

- If `userId` is present, backend uses it to route the sensor data.
- If `userId` is missing, backend attempts to use the authenticated principal.
- Sensor type must match one of `TEMPERATURE`, `HUMIDITY`, `LIGHT`.
- This endpoint is public in the current local-friendly security config.

Success response:

```json
{
  "code": 0,
  "message": "success",
  "timestamp": "2026-06-06T10:30:00"
}
```

## 7. Devices API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{userId}/devices` | JWT | List devices |
| `GET` | `/users/{userId}/devices/{deviceId}` | JWT | Get device detail |
| `POST` | `/users/{userId}/devices/{deviceId}/control` | JWT | Control a device manually |

Device response result:

```json
{
  "id": "device-id",
  "deviceType": "FAN",
  "intensityLevel": 66
}
```

Control request:

```json
{
  "targetValue": 66
}
```

Control behavior:

- Backend clamps value to `0..100`.
- `FAN` keeps the clamped numeric value.
- `LIGHT` becomes `100` when target value is greater than `0`; otherwise `0`.
- A `MANUAL` command is saved.
- Backend publishes a gateway command to `/topic/commands`.

Response result is a `CommandResponse`.

## 8. Commands API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{userId}/commands` | JWT | List command history |
| `GET` | `/users/{userId}/commands/{commandId}` | JWT | Get one command |
| `DELETE` | `/users/{userId}/commands/{commandId}` | JWT | Delete one command |

Command response result:

```json
{
  "id": "command-id",
  "commandType": "MANUAL",
  "device": {
    "id": "device-id",
    "deviceType": "FAN",
    "intensityLevel": 66
  },
  "previousIntensity": 0,
  "currentIntensity": 66,
  "autoRuleId": null,
  "speechInputId": null,
  "createdAt": "2026-06-06T10:30:00"
}
```

## 9. Speech Input API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{userId}/speech-inputs` | JWT | List speech command history |
| `GET` | `/users/{userId}/speech-inputs/{speechInputId}` | JWT | Get one speech input |
| `DELETE` | `/users/{userId}/speech-inputs/{speechInputId}` | JWT | Delete one speech input |
| `POST` | `/users/{userId}/speech-inputs/predict` | JWT | Predict intent and optionally execute command |

Predict request:

```json
{
  "rawtext": "bật quạt"
}
```

Response result:

```json
{
  "id": "speech-input-id",
  "rawtext": "bật quạt",
  "predictLabel": "TURN_ON_FAN",
  "confidence": 0.93,
  "createdAt": "2026-06-06T10:30:00",
  "device": {
    "id": "device-id",
    "deviceType": "FAN",
    "intensityLevel": 100
  },
  "targetValue": 100
}
```

Behavior:

- Blank text is rejected.
- Backend calls AI service using `AI_SERVICE_BASE_URL`.
- Low-confidence or unknown predictions are saved as `UNKNOWN` and do not execute device commands.
- Known labels update device state, save `SPEECH` command, and publish WebSocket command.

## 10. Auto Rules API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{userId}/auto-rules` | JWT | List active/non-deleted rules |
| `POST` | `/users/{userId}/auto-rules` | JWT | Create rule |
| `GET` | `/users/{userId}/auto-rules/{autoRuleId}` | JWT | Get rule |
| `PUT` | `/users/{userId}/auto-rules/{autoRuleId}` | JWT | Update rule |
| `DELETE` | `/users/{userId}/auto-rules/{autoRuleId}` | JWT | Soft delete rule |

Create request:

```json
{
  "operator": "GT",
  "thresh": 30.0,
  "sensorId": "temperature-sensor-id",
  "deviceId": "fan-device-id",
  "targetValue": 100
}
```

Update request:

```json
{
  "operator": "GE",
  "thresh": 29.5,
  "targetValue": 66,
  "active": true
}
```

Response result:

```json
{
  "id": "rule-id",
  "description": "TEMPERATURE GT 30.0 -> FAN 100",
  "active": true,
  "operator": "GT",
  "thresh": 30.0,
  "sensorResponse": {
    "id": "sensor-id",
    "sensorType": "TEMPERATURE",
    "currentValue": 31.2
  },
  "deviceResponse": {
    "id": "device-id",
    "deviceType": "FAN",
    "intensityLevel": 100
  },
  "targetValue": 100,
  "deletedAt": null
}
```

Auto-rule behavior:

- Rules trigger on threshold crossing, not merely while condition is true.
- Scheduler evaluates rules every 5 seconds.
- Cooldown prevents repeated command spam.
- If multiple rules target the same device in one evaluation cycle, backend selects one candidate.
- Delete is soft delete: rule is disabled and `deletedAt` is set.

## 11. WebSocket / STOMP Contract

### Endpoint

```text
ws://localhost:8080/ws
```

### STOMP Frames

Gateway sends:

```text
CONNECT
accept-version:1.2
heart-beat:10000,10000

\0
```

Then subscribes:

```text
SUBSCRIBE
id:smart-room-gateway
destination:/topic/commands

\0
```

### Command Topic

```text
/topic/commands
```

Message body:

```json
{
  "userId": "c7ab5c64-cee4-4ef6-9b2e-1f71824c0920",
  "deviceType": "LIGHT",
  "value": 100
}
```

Gateway maps:

```text
FAN value   -> S<value>
LIGHT > 0   -> 1
LIGHT <= 0  -> 0
```

## 12. AI Service API

Base URL:

```text
http://localhost:8000
```

### Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Predict

```http
POST /predict
Content-Type: application/json
```

Request:

```json
{
  "rawtext": "tắt đèn"
}
```

The AI service also accepts `rawText` as an alias.

Response:

```json
{
  "predictLabel": "TURN_OFF_LIGHT",
  "confidence": 0.91
}
```

Possible system labels:

- `TURN_ON_FAN`
- `TURN_OFF_FAN`
- `TURN_ON_LIGHT`
- `TURN_OFF_LIGHT`
- `UNKNOWN`

## 13. Error Code Families

| Range | Area |
|---:|---|
| `1000-1099` | Common/system errors |
| `1100-1199` | Auth/JWT errors |
| `2000-2099` | User errors |
| `3000-3099` | Sensor errors |
| `4000-4099` | Device errors |
| `5000-5099` | Command errors |
| `6000-6099` | Auto-rule errors |
| `7000-7099` | Speech/ML errors |
| `8000-8099` | Database errors |

Common examples:

| Code | Message | HTTP status |
|---:|---|---|
| `1001` | `Invalid request` | `400` |
| `1002` | `Unauthorized` | `401` |
| `1003` | `Forbidden` | `403` |
| `2000` | `User not found` | `404` |
| `3000` | `Sensor not found` | `404` |
| `4000` | `Device not found` | `404` |
| `6001` | `Invalid rule` | `400` |
| `7003` | `ML service unavailable` | `503` |

## 14. Related Documents

- [Architecture](architecture.md)
- [Setup Guide](setup.md)
- [IoT Edge Guide](iot.md)
- [AI Service Guide](ai-service.md)
- [Environment Variables](env.md)
