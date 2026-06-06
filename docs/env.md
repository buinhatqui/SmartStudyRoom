# Environment Variables

Tài liệu này liệt kê toàn bộ biến môi trường đang được hệ thống sử dụng hoặc được khai báo trong các file `.env.example`.

## 1. Configuration Policy

- Không commit file `.env` thật.
- Chỉ commit `.env.example` với giá trị mẫu hoặc giá trị local an toàn.
- Secret production phải được inject qua environment của nền tảng deploy.
- Mỗi service tự đọc cấu hình của nó; không trộn toàn bộ biến vào một file chung nếu không cần.
- Khi thay đổi tên biến, cập nhật đồng thời:
  - `.env.example`
  - `docs/env.md`
  - `docs/setup.md`
  - deployment notes nếu có

## 2. File Locations

| File | Service | Status |
|---|---|---|
| `backend/.env.example` | Backend | Committed sample |
| `backend/.env` | Backend | Local only |
| `frontend/.env.example` | Frontend | Committed sample |
| `frontend/.env` | Frontend | Local only |
| `ai-service/.env.example` | AI service | Committed sample |
| `ai-service/.env` | AI service | Local only |
| `iot-edge/.env.example` | IoT edge | Committed sample |
| `iot-edge/.env` | IoT edge | Local only |

## 3. Backend

Spring Boot imports local env files through `application.yaml`:

```yaml
spring:
  config:
    import:
      - optional:file:.env[.properties]
      - optional:file:backend/.env[.properties]
```

### Variables

| Variable | Default | Required | Description |
|---|---|---:|---|
| `SERVER_PORT` | `8080` | No | HTTP port for Spring Boot backend |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://localhost:3306/smart_study_room` | Yes | MySQL JDBC URL |
| `SPRING_DATASOURCE_USERNAME` | `root` | Yes | Database username |
| `SPRING_DATASOURCE_PASSWORD` | empty | Yes | Database password |
| `SPRING_JPA_HIBERNATE_DDL_AUTO` | `update` | No | Hibernate schema behavior |
| `JWT_SIGNER_KEY` | `dev-only-change-me...` | Yes | HMAC signer key for JWT |
| `JWT_VALID_DURATION` | `36000` | No | Access token lifetime in seconds |
| `JWT_REFRESHABLE_DURATION` | `360000` | No | Refresh window in seconds |
| `AI_SERVICE_BASE_URL` | `http://localhost:8000` | Yes for speech | Base URL of FastAPI AI service |
| `AI_SERVICE_TIMEOUT_SECONDS` | `2` | No | Timeout for backend-to-AI requests |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Yes for frontend | Comma-separated allowed frontend origins |

### Local Example

```properties
SERVER_PORT=8080
SPRING_DATASOURCE_URL=jdbc:mysql://localhost:3307/smart_study_room
SPRING_DATASOURCE_USERNAME=root
SPRING_DATASOURCE_PASSWORD=smart_room_local_password
SPRING_JPA_HIBERNATE_DDL_AUTO=update
JWT_SIGNER_KEY=replace-with-at-least-32-random-characters
JWT_VALID_DURATION=36000
JWT_REFRESHABLE_DURATION=360000
AI_SERVICE_BASE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT_SECONDS=2
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Production Notes

- Use a high-entropy `JWT_SIGNER_KEY`; do not reuse the demo key from README in production.
- Set `SPRING_JPA_HIBERNATE_DDL_AUTO=validate` or manage schema through migrations when deploying seriously.
- Restrict `CORS_ALLOWED_ORIGINS` to real frontend domains.
- Use a managed secret store or deployment platform environment variables.

## 4. Frontend

Vite exposes only variables prefixed with `VITE_` to browser code.

### Variables

| Variable | Default | Required | Description |
|---|---|---:|---|
| `VITE_API_BASE_URL` | `http://localhost:8080` | Yes | Backend API base URL used by Axios |
| `VITE_DATA_PROVIDER` | `backend` | No | `backend` for project backend, `adafruit` for legacy Adafruit mode |
| `VITE_WS_URL` | unset | No | Optional raw WebSocket URL for legacy realtime hook |
| `VITE_AIO_USERNAME` | empty | Only Adafruit mode | Adafruit IO username |
| `VITE_AIO_KEY` | empty | Only Adafruit mode | Adafruit IO key |
| `VITE_ADAFRUIT_BASE_URL` | `https://io.adafruit.com/api/v2` | Only Adafruit mode | Adafruit IO API base URL |

### Local Example

```properties
VITE_API_BASE_URL=http://localhost:8080
VITE_DATA_PROVIDER=backend
```

### Notes

- Do not place backend secrets or database credentials in frontend env files.
- Any `VITE_*` value is bundled into browser-accessible code.
- The normal runtime path uses REST through backend APIs; Adafruit mode is legacy/optional.

## 5. AI Service

AI service currently reads model configuration from environment variables. Host/port are normally supplied to `uvicorn` from the command line.

### Variables

| Variable | Default | Required | Description |
|---|---|---:|---|
| `AI_MODEL_DIR` | `models` | Yes | Directory containing `vectorizer.pkl`, `selector.pkl`, `model_v1.pkl` |
| `AI_MIN_CONFIDENCE` | `0.7` | No | Minimum confidence before returning `UNKNOWN` |
| `AI_SERVICE_HOST` | `0.0.0.0` in example | No | Documented convenience value for uvicorn host |
| `AI_SERVICE_PORT` | `8000` in example | No | Documented convenience value for uvicorn port |

### Local Example

```properties
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8000
AI_MODEL_DIR=models
AI_MIN_CONFIDENCE=0.7
```

### Notes

- `AI_SERVICE_HOST` and `AI_SERVICE_PORT` are present in `.env.example`, but the current run command passes host/port directly to `uvicorn`.
- If model files move, update `AI_MODEL_DIR`.
- If confidence threshold changes, verify backend speech behavior and tests.

## 6. IoT Edge

IoT edge scripts read variables from the process environment. The current Python scripts do not automatically load `.env`; set variables in the shell or load them before running scripts.

### Variables

| Variable | Default | Required | Description |
|---|---|---:|---|
| `SMART_ROOM_USER_ID` | seeded demo user id | Yes for unauthenticated ingest | Backend user id used to associate sensor/device data |
| `SMART_ROOM_SERIAL_PORT` | `COM3` | Real hardware only | Serial port connected to YoloBit |
| `SMART_ROOM_BAUDRATE` | `115200` | Real hardware only | Serial baudrate |
| `SMART_ROOM_BACKEND_URL` | `http://localhost:8080` | Yes | Backend REST base URL |
| `SMART_ROOM_WS_URL` | `ws://localhost:8080/ws` | Yes for commands | Backend STOMP WebSocket URL |
| `SMART_ROOM_BACKEND_TOKEN` | empty | Optional | Bearer token for backend calls |
| `SMART_ROOM_DEBUG_SERIAL` | `1` | No | `1` prints ignored serial lines; `0` suppresses |
| `SMART_ROOM_SENSOR_INTERVAL` | `5` | Simulator only | Sensor simulator interval in seconds |

### Local Example

```powershell
$env:SMART_ROOM_USER_ID="c7ab5c64-cee4-4ef6-9b2e-1f71824c0920"
$env:SMART_ROOM_SERIAL_PORT="COM3"
$env:SMART_ROOM_BAUDRATE="115200"
$env:SMART_ROOM_BACKEND_URL="http://localhost:8080"
$env:SMART_ROOM_WS_URL="ws://localhost:8080/ws"
$env:SMART_ROOM_DEBUG_SERIAL="1"
```

### Notes

- `SMART_ROOM_USER_ID` must match an existing backend user.
- If `SMART_ROOM_USER_ID` is omitted, `/iot/sensor-data` requires an authenticated request context.
- Use `SMART_ROOM_BACKEND_TOKEN` if backend IoT endpoints are tightened in the future.

## 7. Security Checklist

Before sharing or deploying:

- Confirm `.env` files are ignored by Git.
- Rotate any secret that was accidentally committed.
- Replace demo `JWT_SIGNER_KEY`.
- Use non-root database credentials for deployment.
- Restrict CORS origins.
- Do not expose unauthenticated IoT endpoints to the public internet without gateway authentication or network controls.

## 8. Related Documents

- [Setup Guide](setup.md)
- [Architecture](architecture.md)
- [IoT Edge Guide](iot.md)
- [AI Service Guide](ai-service.md)
