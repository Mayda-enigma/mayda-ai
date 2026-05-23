# Contributing to `mayda-ai`

This repo hosts the AI capabilities consumed by `mayda-backend`:
recommendations, semantic search, inventory forecasting, and voice
processing. They run as a single FastAPI application under
[src/](src/).

## Adding a new endpoint — the 5-step checklist

Every new endpoint MUST do all five things below. They are not optional —
the gateway and the rest of the platform assume them.

1. **Protect it with `require_service_token`.** Public probes (e.g.
   `/api/health`) are the only exceptions. See
   [docs/conventions/service-token.md](docs/conventions/service-token.md).
   ```python
   @router.post("/foo", dependencies=[Depends(require_service_token)])
   ```

2. **Propagate `X-Request-Id`.** Read it off `request.state.request_id` and
   forward it to any downstream `BackendAPIClient` call. See
   [docs/conventions/request-id.md](docs/conventions/request-id.md).

3. **Read config from `src.core.config.settings`.** Never call `os.getenv`
   directly in route code. New env vars belong in
   [src/core/config.py](src/core/config.py) and
   [docs/conventions/env-vars.md](docs/conventions/env-vars.md), with a
   sample in [.env.example](.env.example).

4. **Use Pydantic schemas for request and response.** Put them under
   [src/schemas/](src/schemas/). Don't return raw dicts.

5. **Log via the stdlib `logging.getLogger(__name__)`.** No `print()`. Include
   the request ID and any user/restaurant identifiers in the log line.

## Local development

```bash
uv sync
cp .env.example .env   # fill in keys
uv run uvicorn src.main:app --reload
```

The app exposes Swagger UI at `http://localhost:8101/docs`.

## Architectural notes

- `mayda-ai` is **one** FastAPI application, not four. The original plan in
  [docs/issues.md](docs/issues.md) describes a four-service split that was
  collapsed into the current consolidated layout. New work should follow the
  consolidated layout.
- Cross-cutting middleware lives at [src/middleware/](src/middleware/). Wire
  it in [src/main.py](src/main.py), in this order:
  1. `RequestIdMiddleware` (outermost — wraps everything else)
  2. `CORSMiddleware`
- Long-lived dependencies (HTTP client, ChromaDB, forecaster, Whisper) live on
  `app.state` and are initialised inside the `lifespan` context manager.

## Commit style

We follow conventional-ish commits with a ticket tag prefix:

```
[AI-002] Document canonical service-token pattern
```

One commit per task. Don't batch. Run lint/tests before pushing.

## Conventions index

- [Service-token validation](docs/conventions/service-token.md)
- [Request-ID propagation](docs/conventions/request-id.md)
- [Environment variables](docs/conventions/env-vars.md)
- [CORS policy](docs/conventions/cors.md)
