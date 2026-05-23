# Service-token validation (`X-Service-Token`)

Every endpoint exposed by `mayda-ai` is reachable only from `mayda-backend`. Any
request that does not carry a valid `X-Service-Token` header must be rejected
with `401`.

## Canonical pattern

```python
from fastapi import Header, HTTPException
import os

SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")


async def require_service_token(x_service_token: str | None = Header(None)):
    if not SERVICE_TOKEN or x_service_token != SERVICE_TOKEN:
        raise HTTPException(401, "Invalid service token")
```

A copy-paste helper lives at [docs/snippets/service_auth.py](../snippets/service_auth.py).
The production implementation in this repo lives at
[src/middleware/service_auth.py](../../src/middleware/service_auth.py).

## How to apply it on an endpoint

```python
from fastapi import APIRouter, Depends
from src.middleware.service_auth import require_service_token

router = APIRouter()

@router.post(
    "/recommendations",
    dependencies=[Depends(require_service_token)],
)
async def post_recommendations(...):
    ...
```

Public probes (e.g. `/api/health`) must NOT include the dependency — they need
to stay reachable for the gateway's liveness checks.

## Forwarding to downstream calls

When `mayda-ai` calls back into `mayda-backend`, it must forward the same token
header so the backend can authenticate the call:

```python
headers = {"X-Service-Token": settings.SERVICE_TOKEN}
await client.get(f"{backend_url}/users/{user_id}/profile", headers=headers)
```

See [src/services/backend_client.py](../../src/services/backend_client.py) for
the canonical outbound client.

## Dev-mode behaviour

When `SERVICE_TOKEN` is empty the dependency short-circuits without raising —
this keeps local development friction-free. In production the env var MUST be
set; the gateway will fail-close if it can't authenticate.
