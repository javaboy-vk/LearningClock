# LearningClock HTTP API

LearningClock exposes a small FastAPI application for runtime and integration checks. Its API
version follows the LearningClock package version.

## Start the API

Install the project dependencies, then launch the development server from the repository root:

```cmd
dev install
dev api --reload
```

The default server address is `http://127.0.0.1:8000`.

| Resource | URL |
| --- | --- |
| Health endpoint | `http://127.0.0.1:8000/health` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |

Use `dev api --host <address> --port <port>` to select a different bind address or port. Do not
bind the development server to an externally reachable interface without reviewing access and
deployment controls.

## Export the OpenAPI contract

Regenerate the tracked schema after changing API metadata, request models, response models, or
routes:

```cmd
dev openapi
```

The command writes `docs\openapi.json` directly from `learningclock.api.app.openapi()` so the
checked-in contract and the runtime Swagger UI use the same source.

## Current endpoint

`GET /health` returns readiness and package-version metadata:

```json
{
  "status": "ready",
  "version": "6.0"
}
```
