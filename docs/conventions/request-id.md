# Request-ID propagation (`X-Request-Id`)

Every request entering `mayda-ai` must carry an `X-Request-Id`. The gateway
generates one if the caller did not, then forwards it. Inside the service we:

1. Read `X-Request-Id` off the inbound request (or generate a UUID if absent).
2. Stash it on `request.state.request_id` so route handlers can log with it.
3. Echo it back on the response so the client can correlate.
4. Forward it on any outbound call to `mayda-backend` so backend logs join the
   same trace.

## Canonical middleware

```python
import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
```

The production implementation is at
[src/middleware/request_id.py](../../src/middleware/request_id.py).

Register it as the **outermost** middleware so it wraps everything (CORS,
auth, route handlers):

```python
app.add_middleware(RequestIdMiddleware)
app.add_middleware(CORSMiddleware, ...)
```

## Using the request ID in route handlers

```python
from fastapi import Request

@router.post("/recommendations")
async def post_recommendations(req: Request, body: RecommendRequest):
    request_id = getattr(req.state, "request_id", None)
    return await service.recommend(body, request_id=request_id)
```

## Forwarding to downstream calls

`BackendAPIClient` accepts an optional `request_id` on every method and sets it
in the outbound `X-Request-Id` header (see
[src/services/backend_client.py](../../src/services/backend_client.py)).
Always forward it — that's how a single user action gets one continuous trace
across services.

## Logging

Include the request ID in any log line that describes work done for a request.
The standard format makes it easy to grep:

```
"%(asctime)s | %(levelname)-8s | %(name)s | req=%(request_id)s | %(message)s"
```
