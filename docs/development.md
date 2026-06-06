# Development Guide

Tài liệu này mô tả quy ước phát triển, cách kiểm thử và các nguyên tắc khi đóng góp vào Smart Study Room.

## 1. Development Principles

- Prefer existing module boundaries over cross-cutting shortcuts.
- Keep backend DTO contracts stable because frontend maps directly from them.
- Keep IoT protocol changes explicit and documented.
- Keep AI model label changes synchronized with backend intent mapping.
- Do not commit generated dependencies or build outputs.
- Update docs when changing runtime behavior, API contract or setup steps.

## 2. Branch and Commit Guidelines

Recommended branch naming:

```text
feature/<short-name>
fix/<short-name>
docs/<short-name>
refactor/<short-name>
```

Commit messages should state the behavior being changed:

```text
docs: expand IoT gateway guide
fix: normalize light command values
feat: add humidity auto-rule support
```

## 3. Generated Files

Do not commit:

```text
frontend/node_modules/
frontend/dist/
frontend/.vite/
backend/target/
ai-service/.venv/
ai-service/venv/
__pycache__/
*.pyc
```

Keep committed:

```text
frontend/package.json
frontend/package-lock.json
backend/pom.xml
ai-service/requirements.txt
iot-edge/requirements.txt
*.env.example
```

## 4. Local Checks

Full check:

```powershell
.\scripts\test.ps1
```

Equivalent manual checks:

```powershell
cd backend
mvn test
```

```powershell
cd frontend
npm run build
```

```powershell
cd ai-service
python -m py_compile service.py app\*.py tests\*.py
python -m unittest discover -s tests
```

```powershell
cd iot-edge
python -m py_compile gateway.py app\*.py tests\*.py
python -m unittest discover -s tests
```

## 5. Test Strategy

| Area | Current checks | Recommended additions |
|---|---|---|
| Backend services | Spring tests for application and auto rules | Controller tests, auth tests, repository edge cases |
| Frontend | TypeScript build | Component tests, API mapper tests, route guard tests |
| AI service | Preprocessing tests | Model contract tests, confidence threshold tests |
| IoT edge | Parser tests | STOMP frame parsing tests, backend client mocks |
| End-to-end | Manual scripts | Automated smoke test with simulator |

## 6. Backend Development Notes

### Package boundaries

| Package | Rule of thumb |
|---|---|
| `controller/` | HTTP contract only; keep business logic in services |
| `service/` | Business rules, validation, transactions |
| `repository/` | Data access only |
| `dto/` | API request/response contracts |
| `mapper/` | Entity/DTO mapping |
| `configuration/` | Framework and infrastructure configuration |

### API changes

When changing backend API:

1. Update DTOs/controllers.
2. Update frontend feature API client.
3. Update `docs/api.md`.
4. Run backend tests.
5. Run frontend build.

### Authorization changes

Check:

- Public endpoints in `SecurityConfig`.
- Method-level `@PreAuthorize` checks.
- Frontend route guards.
- Admin/user behavior.

## 7. Frontend Development Notes

### Structure

Use feature APIs under `frontend/src/features/*/api.ts` for backend interaction. `frontend/src/services/api.ts` works as a compatibility barrel.

### API client

The shared Axios client:

- Uses `VITE_API_BASE_URL`.
- Adds JWT token from local storage.
- Redirects to `/login` on `401`.
- Unwraps backend `ApiResponse<T>`.

### Routing

Route definitions are centralized in `frontend/src/app/App.tsx`.

When adding a page:

1. Add page under `frontend/src/pages/`.
2. Add route in `App.tsx`.
3. Add API/model under `features/` if needed.
4. Keep admin-only pages behind admin route guard.

## 8. IoT Development Notes

Prefer updating `iot-edge/app/*` modules instead of editing everything inside `gateway.py`.

When changing serial protocol:

1. Update `iot-edge/app/parser.py`.
2. Update gateway/simulator behavior if needed.
3. Add/update `iot-edge/tests/test_parser.py`.
4. Update [IoT Edge Guide](iot.md).
5. Test with simulator before real hardware.

## 9. AI Development Notes

When changing model behavior:

1. Keep model artifacts compatible.
2. Update `LABEL_MAPPING` in `ai-service/app/model.py`.
3. Update backend `SpeechInputService.parseIntent()` if system labels change.
4. Update [AI Service Guide](ai-service.md).
5. Run AI tests and backend speech flow manually.

## 10. Documentation Standards

Documentation should include:

- Purpose and scope.
- Exact commands that can be copied.
- Expected output or response shape.
- Configuration variables.
- Failure modes and troubleshooting.
- Related documents.

Prefer diagrams for workflows that cross service boundaries.

## 11. Release / Handoff Checklist

Before handing off a milestone:

- `README.md` reflects current project scope.
- `docs/` reflects current setup/API/runtime behavior.
- `.\scripts\test.ps1` passes or known failures are documented.
- `.env.example` files are up to date.
- Generated folders are not staged.
- Secrets are not committed.
- Hardware protocol changes are tested with simulator and, when possible, real YoloBit.

## 12. Common Change Playbooks

### Add a new REST endpoint

1. Add request/response DTOs if needed.
2. Add controller method.
3. Implement service logic.
4. Add repository method if needed.
5. Add frontend API wrapper.
6. Add tests based on risk.
7. Update API docs.

### Add a new auto-rule behavior

1. Update `AutoRuleService`.
2. Verify threshold crossing semantics.
3. Verify cooldown behavior.
4. Add tests for edge cases.
5. Update architecture/API docs if behavior changes.

### Add a new voice command

1. Update dataset/model and label mapping.
2. Update backend intent mapping.
3. Verify target device/value mapping.
4. Update AI docs and API docs if new label is public.
5. Run manual end-to-end speech test.

## 13. Related Documents

- [Documentation Home](README.md)
- [Architecture](architecture.md)
- [Setup Guide](setup.md)
- [API Reference](api.md)
- [IoT Edge Guide](iot.md)
- [AI Service Guide](ai-service.md)
