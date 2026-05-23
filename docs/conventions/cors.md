# CORS policy: gateway only

`mayda-ai` is a back-of-house service. The only browser origin that should ever
reach it directly is the gateway / frontend dev server. Wildcard `["*"]` is
forbidden — it would let any tab on the internet call our endpoints.

## Canonical configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.GATEWAY_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`GATEWAY_ORIGIN` is read from the environment. In dev it points at the
frontend dev server (`http://localhost:3000`); in prod it's the deployed
gateway origin.

Production implementation: [src/main.py](../../src/main.py).

## Multiple origins

If a service legitimately needs to accept more than one origin (e.g. preview
deploys), extend `GATEWAY_ORIGIN` to a comma-separated list and split it in
config — do not fall back to `["*"]`.

## Pre-flight headers

`allow_headers=["*"]` permits `X-Service-Token` and `X-Request-Id` to ride on
preflight responses. If you tighten this list, add those two explicitly or
auth/tracing will break silently from the browser.
