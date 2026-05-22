Here's the full operational plan: **38 issues** covering the 4 AI services + repo-level scaffolding. Same format as before.

Issue ID prefixes:
- `AI-` = mayda-ai repo-level
- `RC-` = recommendation service
- `SR-` = search service
- `IN-` = inventory service
- `VC-` = voice service

---

# 🗂️ REPO: `mayda-ai` — Foundation Issues

### ISSUE AI-001: Initialize `mayda-ai` monorepo with 4 service subfolders

**Description**
Create the `mayda-ai` repo and import each of the 4 AI service folders as siblings under the repo root. Pragmatic approach: fresh `git init` (history of individual services lost but code preserved) — the 4 source folders are each their own git repo, and consolidating with `git subtree` would cost hours that the 48h budget can't spare.

**Goal**
Single `mayda-ai` repo with `recommendation/`, `search/`, `inventory/`, `voice/` subfolders, all buildable.

**Targeted Files**
- New repo: `mayda-ai/`
- `recommendation/` (from `Recommendation_system_for_meals/recommendation-service/`)
- `search/` (from `search-llm/`)
- `inventory/` (from `Inventory_prediction/`)
- `voice/` (from `Voice-Chef---AI-Voice-Interface-for-Restaurant-Orders/`)
- Root `README.md`, `.gitignore`

**Tasks**
- [ ] Create GitHub repo `mayda/mayda-ai` (public)
- [ ] Copy each source folder into its target subdir (rename in the process)
- [ ] Strip out each source folder's `.git/` directory after copy
- [ ] Move recommendation's `recommendation-service/*` to top-level `recommendation/`; archive parent legacy (`llm_recommendation_engine.py`, `user_profile_service.py`, `test_*.py`, `mock_database/`) into `recommendation/legacy/`
- [ ] Root `README.md` documenting the 4-service layout, ports (8101/8102/8103/8104), per-service dev commands
- [ ] Root `.gitignore` covering Python + Docker + DB defaults

**Acceptance Criteria**
- `git clone` produces a working tree with all 4 services
- Each service's existing dev command works (`docker compose up` in recommendation + search; CLI in inventory + voice)
- No nested `.git/` folders remain

**References**
- AUDIT.md → "Repository Overview"
- Architecture Foundation → repo layout

**Blocked By**
- None

---

### ISSUE AI-002: Establish shared service-token middleware pattern + CONTRIBUTING.md

**Description**
All 4 AI services need identical `X-Service-Token` header validation to reject any traffic that doesn't come from `mayda-backend`. Document the pattern once and provide a copy-paste-ready helper that each service includes.

**Goal**
Single source of truth for service-token validation; each service uses the same 5-line guard.

**Targeted Files**
- `docs/conventions/service-token.md`
- `docs/conventions/request-id.md`
- `CONTRIBUTING.md`
- Helper sketch in `docs/snippets/service_auth.py`

**Tasks**
- [ ] Document the canonical pattern:
  ```python
  from fastapi import Header, HTTPException
  import os
  SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")
  async def require_service_token(x_service_token: str | None = Header(None)):
      if not SERVICE_TOKEN or x_service_token != SERVICE_TOKEN:
          raise HTTPException(401, "Invalid service token")
  ```
- [ ] Document the request-ID forwarding pattern (read `X-Request-Id`, store in logs, echo back)
- [ ] Document the standard env vars every service must accept: `SERVICE_TOKEN`, `LOG_LEVEL`, `PORT`
- [ ] Document CORS pattern (gateway-only origin)
- [ ] `CONTRIBUTING.md` lists the 5 things any new endpoint must do

**Acceptance Criteria**
- Any contributor can read the doc and add a service-token-protected endpoint in < 10 minutes
- All 4 services will reference this doc in their own READMEs

**References**
- AUDIT.md → "What's universally broken across all 4 services"

**Blocked By**
- None

---

### ISSUE AI-003: Per-service CI matrix with path filtering

**Description**
Avoid rebuilding all 4 service Docker images on every push. Use `dorny/paths-filter` to detect which service changed and only build/test that one.

**Goal**
CI under 4 minutes for single-service changes.

**Targeted Files**
- `.github/workflows/ci.yml`

**Tasks**
- [ ] `dorny/paths-filter@v3` job detecting changes per `{recommendation,search,inventory,voice}/**`
- [ ] Matrix `build` job per changed service: `docker build` + run tests if `tests/` exists
- [ ] Cache Docker layers per service
- [ ] Lint Python with `ruff` per changed service

**Acceptance Criteria**
- Touching `recommendation/**` triggers only the recommendation job
- All 4 services run in parallel when all changed
- Lint failures fail CI

**References**
- AUDIT.md → "Cross-Service Summary"
- [dorny/paths-filter](https://github.com/dorny/paths-filter)

**Blocked By**
- AI-001

---

### ISSUE AI-004: Root `docker-compose.yml` orchestrating all 4 services + their DBs

**Description**
Single command (`docker compose up`) brings up all 4 AI services + their isolated databases on the canonical ports. Each service has its own `docker-compose.yml` for standalone dev; this root one wires everything together for integration testing alongside the backend.

**Goal**
One `docker compose up` from `mayda-ai/` boots the full AI tier.

**Targeted Files**
- `docker-compose.yml` (root)
- `.env.example` (shared service token + DB passwords)

**Tasks**
- [ ] Define services: `recommendation` (8101), `search` (8102), `inventory` (8103), `voice` (8104)
- [ ] Define databases: `rec-db` (Postgres 5433), `redis` (6379)
- [ ] Define shared volumes: `chroma_data`, `inventory_data`, `hf_cache`
- [ ] Define shared network `mayda_ai_network`
- [ ] All services receive `SERVICE_TOKEN` from `.env`
- [ ] All services receive `BACKEND_API_URL=http://host.docker.internal:8001` (or `gateway:8001` if running with the full mayda-infra stack)
- [ ] Add `healthcheck` stanza for each service

**Acceptance Criteria**
- `docker compose up` brings all 4 services + DBs to healthy state
- `curl localhost:8101/health`, `:8102/health`, `:8103/health`, `:8104/health` all return 200
- Stopping one service doesn't kill the others

**References**
- AI-002
- AUDIT.md cross-service summary

**Blocked By**
- AI-001, RC-008, SR-008, IN-003, VC-009

---

# 🔵 SERVICE: `recommendation`

### ISSUE RC-001: Migrate folder + archive legacy parent-folder code

**Description**
The `recommendation/` service lives under `recommendation-service/` in the original repo, with 1,682 lines of pre-pivot orphaned code in the parent folder (legacy engine, test files, mock database). Move the active service to top-level `recommendation/` and archive the legacy material so it's preserved but doesn't ship in the Docker image.

**Goal**
Clean folder structure with active service at top level and legacy isolated.

**Targeted Files**
- `recommendation/` (active service files moved here)
- `recommendation/legacy/` (legacy parent files)
- `recommendation/legacy/README.md`
- `recommendation/.dockerignore`

**Tasks**
- [ ] Move contents of `Recommendation_system_for_meals/recommendation-service/*` → `recommendation/`
- [ ] Move `Recommendation_system_for_meals/llm_recommendation_engine.py`, `user_profile_service.py`, `test_*.py`, `mock_database/`, `API_MIGRATION_NOTES.md`, `DATABASE_API_REQUIREMENTS.md`, `RECOMMENDATION_SYSTEM_INSTRUCTIONS.md` → `recommendation/legacy/`
- [ ] Write `legacy/README.md` explaining: "Pre-pivot artifacts from the original recommendation repo. Not loaded by the running service. Kept for reference."
- [ ] Add `legacy/` to `.dockerignore`

**Acceptance Criteria**
- `recommendation/` is buildable without `legacy/`
- `docker build` doesn't copy legacy into the image (verify with `docker image inspect`)
- README clear about non-buildable status

**References**
- AUDIT.md → "1,682 lines of dark legacy code"

**Blocked By**
- AI-001

---

### ISSUE RC-002: Standardize service port to 8101 across all configs

**Description**
The service currently listens on 8000 internally and is mapped to 8001 externally — both wrong vs. architecture (8101). Update Dockerfile, docker-compose, lifespan logs, and `__main__` block.

**Goal**
Port 8101 used consistently.

**Targeted Files**
- `recommendation/app/main.py`
- `recommendation/Dockerfile`
- `recommendation/docker-compose.simple.yml`
- `recommendation/README.md`

**Tasks**
- [ ] `app/main.py`: `__main__` block → `port=8101`
- [ ] `Dockerfile`: `EXPOSE 8101`, healthcheck → `http://localhost:8101/health`, CMD → `--port 8101`
- [ ] `docker-compose.simple.yml`: port mapping → `"8101:8101"`
- [ ] Update README with new dev command

**Acceptance Criteria**
- `curl localhost:8101/health` returns 200 in dev + Docker
- Port 8000 no longer referenced anywhere in the service

**References**
- AUDIT.md → "Cross-Service Summary" port table
- Architecture Foundation port allocation

**Blocked By**
- AI-001

---

### ISSUE RC-003: Reshape endpoint to `POST /recommendations` matching backend contract

**Description**
Backend's `/ai/recommend` proxy (BE-005) sends `POST` with body `{user_id, cart_item_ids, time_of_day}`. Current service exposes `GET /api/v1/recommendations/{user_id}?limit=&restaurant_id=`. Either side has to give — change the service to match the gateway contract (clients shouldn't dictate gateway routes).

**Goal**
Service contract matches backend proxy expectation.

**Targeted Files**
- `recommendation/app/main.py`
- `recommendation/app/models.py` (new — request/response schemas)
- `recommendation/app/services/simple_recommendation_engine.py`

**Tasks**
- [ ] Create `app/models.py` with `RecommendRequest`, `Recommendation`, `RecommendResponse` Pydantic models
- [ ] Replace `GET /api/v1/recommendations/{user_id}` with `POST /recommendations`
- [ ] Body schema: `{user_id: int, cart_item_ids: list[int] = [], time_of_day: str | None = None, limit: int = 5, restaurant_id: int | None = None}`
- [ ] Response: `{recommendations: [{dish_id, score, rationale}], generated_at, model}`
- [ ] Update `simple_recommendation_engine.get_recommendations()` signature to accept new inputs
- [ ] Keep `GET /api/v1/recommendations/{user_id}` as deprecated alias for one release (return 308 redirect)

**Acceptance Criteria**
- `curl -X POST localhost:8101/recommendations -d '{"user_id":1}' -H "Content-Type: application/json"` returns recommendations
- Backend `BE-005` proxy successfully calls service and returns parsed JSON
- OpenAPI docs at `/docs` show the new endpoint

**References**
- Backend issue BE-005
- AUDIT.md → "Endpoint contract mismatch"

**Blocked By**
- RC-001

---

### ISSUE RC-004: Add service-token middleware on `/recommendations`

**Description**
Anyone with network access can currently hit the service. Add the shared `X-Service-Token` validation pattern from AI-002 so only the backend gateway can call.

**Goal**
Service rejects requests missing or with invalid `X-Service-Token`.

**Targeted Files**
- `recommendation/app/middleware/service_auth.py` (new)
- `recommendation/app/main.py`
- `recommendation/app/core/config.py`
- `recommendation/.env.example`

**Tasks**
- [ ] Add `SERVICE_TOKEN: str = ""` to `config.py` (required, no default)
- [ ] Create `app/middleware/service_auth.py` with `require_service_token` dependency per AI-002 pattern
- [ ] Apply as dependency on `POST /recommendations` route
- [ ] Skip auth on `/health` and `/` (root)
- [ ] Document `SERVICE_TOKEN` in `.env.example`

**Acceptance Criteria**
- Request without `X-Service-Token` returns 401
- Request with wrong token returns 401
- Request with correct token returns recommendations
- `/health` still public

**References**
- AI-002

**Blocked By**
- AI-002, RC-003

---

### ISSUE RC-005: Fix CORS, exception handling, and encoding bug

**Description**
Three small but real bugs from the audit: CORS is `["*"]`, exceptions return 200 with `{"error": ...}` (breaks status-code semantics), and `main.py:35` has a broken emoji character causing potential UnicodeError.

**Goal**
Clean error responses + proper CORS + valid Unicode.

**Targeted Files**
- `recommendation/app/main.py`

**Tasks**
- [ ] Replace `allow_origins=["*"]` with `allow_origins=[settings.GATEWAY_ORIGIN]` (add to config; default to backend URL)
- [ ] In `POST /recommendations`, replace `return {"error": ..., "user_id": ...}` with `raise HTTPException(status_code=500, detail=...)` for unexpected errors
- [ ] Distinguish: 404 if user not found, 502 if Gemini failed, 504 if Gemini timed out, 500 for everything else
- [ ] Replace broken emoji on line 35 (` Shutting down`) with `"Shutting down..."` (no emoji) or fix encoding

**Acceptance Criteria**
- `Access-Control-Allow-Origin` on responses matches gateway origin
- Failed recommendation returns 5xx (not 200), preserves `X-Request-Id`
- No `UnicodeError` logs on shutdown

**References**
- AUDIT.md → "Code Review — Bottleneck Patterns" for recommendation

**Blocked By**
- RC-001

---

### ISSUE RC-006: Standardize on `httpx`; rewrite backend client to match real backend endpoints

**Description**
Two HTTP client libraries (`aiohttp` + `httpx`) coexist in `requirements.txt`. Also the `backend_client.py` calls non-existent endpoints (`/users/{id}/profile` returning `{preferences, orderHistory, reviews}` shape that mayda-backend doesn't provide). Standardize on `httpx` and align with real backend routes.

**Goal**
Single HTTP client; backend calls succeed against actual backend.

**Targeted Files**
- `recommendation/app/services/backend_client.py`
- `recommendation/requirements.txt`

**Tasks**
- [ ] Rewrite `BackendAPIClient` using `httpx.AsyncClient` (drop `aiohttp`)
- [ ] Map methods to real backend endpoints:
  - `get_user_profile(user_id)` → `GET /api/auth/users/{id}` (if exists) or compose from existing routes
  - `get_user_order_history(user_id)` → `GET /api/orders?userId={id}`
  - `get_user_reviews(user_id)` → `GET /api/reviews?userId={id}`
  - `get_dishes(restaurant_id)` → `GET /api/restaurants/{id}/menus` (returns nested dishes)
  - `log_recommendation_interaction(...)` → defer until backend adds `/analytics/interactions` (BE-016 area)
- [ ] Remove `aiohttp` from `requirements.txt`
- [ ] Forward `X-Service-Token` on every outbound backend call

**Acceptance Criteria**
- No `aiohttp` import remains; only `httpx`
- All backend calls succeed against running backend (verify with integration test)
- 404 from backend handled gracefully (returns empty dict, logs warning)

**References**
- AUDIT.md → "Two HTTP libraries", "Backend client calls non-existent endpoints"

**Blocked By**
- RC-001, mayda-backend endpoints exist

---

### ISSUE RC-007: Propagate `X-Request-Id` from gateway through to logs + backend calls

**Description**
Backend sends `X-Request-Id` on every proxied call (after BE-012). Service should log it on every line and forward it on any outbound backend call.

**Goal**
End-to-end traceability via request ID.

**Targeted Files**
- `recommendation/app/middleware/request_id.py` (new)
- `recommendation/app/main.py`
- `recommendation/app/services/backend_client.py`

**Tasks**
- [ ] Create `RequestIdMiddleware` per AI-002 pattern: read `X-Request-Id` from headers or generate UUID, store on `request.state.request_id`, echo in response header
- [ ] Register middleware in `main.py`
- [ ] Inject request ID into log records (use `loguru` `contextualize` or stdlib `LoggerAdapter`)
- [ ] `BackendAPIClient` accepts `request_id` parameter on each call and forwards as `X-Request-Id`

**Acceptance Criteria**
- Every response has `X-Request-Id` header
- Service logs show request ID on every line per request
- Backend logs show the same ID

**References**
- Backend issue BE-012
- AI-002

**Blocked By**
- AI-002, RC-001

---

### ISSUE RC-008: Update `docker-compose.simple.yml` for root orchestration

**Description**
Rename/restructure compose file so it integrates with the root `mayda-ai/docker-compose.yml` (AI-004) while still working standalone.

**Goal**
Compose entry usable both standalone and as a fragment in the root stack.

**Targeted Files**
- `recommendation/docker-compose.yml` (renamed from `.simple.yml`)
- `recommendation/.env.example`
- `recommendation/README.md`

**Tasks**
- [ ] Rename `docker-compose.simple.yml` → `docker-compose.yml`
- [ ] Service name: `recommendation` (not `recommendation-service`)
- [ ] Add network alias `recommendation` for inter-service discovery
- [ ] Add `redis` and `rec-db` services to standalone compose
- [ ] Set port to `8101:8101`
- [ ] Document `SERVICE_TOKEN`, `BACKEND_API_URL`, `GEMINI_API_KEY` in `.env.example`

**Acceptance Criteria**
- `cd recommendation && docker compose up` brings up the service + Redis + Postgres
- Root `mayda-ai/docker-compose.yml` can reference this service via build context

**References**
- AI-004
- Existing: [docker-compose.simple.yml](Recommendation_system_for_meals/recommendation-service/docker-compose.simple.yml)

**Blocked By**
- RC-002

---

# 🟢 SERVICE: `search`

### ISSUE SR-001: Migrate folder + reorganize into `app/` package structure

**Description**
Current source files (`main.py`, `chromadb_helper.py`, `model.py`, etc.) sit at the top level with no package structure — imports rely on PYTHONPATH magic. Reorganize into `app/` package and archive the 250-line `dish_search_example.py` out of the build context.

**Goal**
Clean package structure; example/test code out of production image.

**Targeted Files**
- `search/app/main.py` (from `search-llm/main.py`)
- `search/app/{chromadb_helper,model,generate_embeddings,database_helper}.py`
- `search/app/__init__.py`
- `search/examples/dish_search_example.py` (moved)
- `search/.dockerignore`

**Tasks**
- [ ] Create `search/app/` package with `__init__.py`
- [ ] Move all `*.py` source files into `app/`
- [ ] Update intra-package imports: `from chromadb_helper import ...` → `from app.chromadb_helper import ...`
- [ ] Move `dish_search_example.py` → `search/examples/`
- [ ] Add `examples/` and `chroma_db/` to `.dockerignore`
- [ ] Update Dockerfile `COPY . .` to copy only `app/`, `requirements.txt`, etc.

**Acceptance Criteria**
- `docker build` succeeds with no `examples/` in image
- All imports work (run server, hit endpoints)
- `python -m app.main` works locally

**References**
- AUDIT.md → "Module imports as bare names"

**Blocked By**
- AI-001

---

### ISSUE SR-002: Fix duplicate `lifespan` + `app = FastAPI(...)` declarations

**Description**
The 354-line `main.py` declares the lifespan function AND the FastAPI app **twice** (lines 34-48 and 99-113). The second declaration silently overwrites the first. Currently harmless because the duplicates are identical — but any middleware added between them would be lost.

**Goal**
Single lifespan function, single FastAPI app instance.

**Targeted Files**
- `search/app/main.py`

**Tasks**
- [ ] Delete lines 96-113 of `main.py` (the duplicate `from contextlib import asynccontextmanager`, second `lifespan`, second `app = FastAPI(...)`)
- [ ] Verify the first `lifespan` is the one bound to the surviving `app`
- [ ] Run server, verify all 9 endpoints still register

**Acceptance Criteria**
- `grep -c "lifespan" main.py` returns matches only in one logical block
- `grep -c "app = FastAPI" main.py` returns exactly 1
- `/docs` lists all 9 endpoints

**References**
- AUDIT.md → "DUPLICATE lifespan function AND DUPLICATE app declarations"

**Blocked By**
- SR-001

---

### ISSUE SR-003: Standardize port to 8102; delete redundant `start_server.py`

**Description**
Port is currently 8000 internal, mapped to 8888 externally — non-standard. Also `start_server.py` duplicates the Dockerfile's CMD and hardcodes `127.0.0.1` (won't bind in containers). Delete it.

**Goal**
Port 8102 everywhere; one way to start the server (the Dockerfile CMD or `python -m app.main`).

**Targeted Files**
- `search/app/main.py`
- `search/Dockerfile`
- `search/docker-compose.yml`
- `search/start_server.py` (DELETE)
- `search/README.md`

**Tasks**
- [ ] `app/main.py`: `__main__` block → `host="0.0.0.0", port=8102`
- [ ] `Dockerfile`: `EXPOSE 8102`, `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8102"]`
- [ ] `docker-compose.yml`: port mapping `"8102:8102"`
- [ ] Delete `start_server.py`
- [ ] Update README

**Acceptance Criteria**
- `curl localhost:8102/health` returns 200 in dev + Docker
- Ports 8000 and 8888 no longer referenced
- `start_server.py` deleted

**References**
- AUDIT.md → "Port chaos"

**Blocked By**
- SR-001

---

### ISSUE SR-004: Pin all dependencies with explicit versions

**Description**
`requirements.txt` lists dependencies with no version constraints (`fastapi`, `uvicorn`, `chromadb`, `sentence-transformers`, etc.). Non-reproducible builds. Pin every one.

**Goal**
Deterministic builds; explicit version control.

**Targeted Files**
- `search/requirements.txt`
- `search/requirements-dev.txt` (new — for ruff/pytest)

**Tasks**
- [ ] Run `pip freeze` in a working container to capture current versions
- [ ] Pin every dep in `requirements.txt` with `==X.Y.Z`
- [ ] Add upper bounds for major versions (e.g. `chromadb>=0.4,<0.5`)
- [ ] Split dev deps into `requirements-dev.txt`

**Acceptance Criteria**
- `pip install -r requirements.txt` produces identical versions on every machine
- `docker build` is reproducible

**References**
- AUDIT.md → "Unpinned dependencies"

**Blocked By**
- SR-001

---

### ISSUE SR-005: Add CORS + service-token middleware

**Description**
Currently no CORS middleware and no auth. Add CORS restricted to backend origin + the shared service-token guard from AI-002.

**Goal**
Only authenticated gateway calls allowed; CORS limited to gateway origin.

**Targeted Files**
- `search/app/main.py`
- `search/app/middleware/service_auth.py` (new)
- `search/app/config.py` (new — settings)
- `search/.env.example`

**Tasks**
- [ ] Create `app/config.py` with `Settings` (pydantic-settings): `SERVICE_TOKEN`, `GATEWAY_ORIGIN`
- [ ] Create `app/middleware/service_auth.py` per AI-002 pattern
- [ ] Add CORS middleware to `main.py` with `allow_origins=[settings.GATEWAY_ORIGIN]`
- [ ] Apply `require_service_token` dependency to all mutation + search endpoints
- [ ] Skip auth on `/health`
- [ ] Document env vars

**Acceptance Criteria**
- Request without token returns 401 on protected endpoints
- `/health` still public
- Browser preflight from gateway origin succeeds
- Random origin preflight fails

**References**
- AI-002

**Blocked By**
- AI-002, SR-002

---

### ISSUE SR-006: Add `POST /search` matching backend contract

**Description**
Backend's `/ai/search` proxy (BE-006) sends `POST` with `{query, restaurant_id?, limit?}`. Service has multiple search-related endpoints; surface a single clean `POST /search` matching the gateway contract.

**Goal**
Clean public search endpoint matching gateway expectation.

**Targeted Files**
- `search/app/main.py`
- `search/app/models.py` (new)

**Tasks**
- [ ] Create `app/models.py` with `SearchRequest`, `SearchResult`, `SearchResponse`
- [ ] Add `POST /search` accepting `{query: str, restaurant_id: int | None, limit: int = 10}`
- [ ] Route uses existing `multilingual_model` + `chroma_db.search_similar`
- [ ] Returns `{results: [{dish_id, score, name, restaurant_name}], language_detected}`
- [ ] Keep existing CRUD endpoints (backend calls them on dish mutations — SR-007)

**Acceptance Criteria**
- `curl -X POST localhost:8102/search -d '{"query":"spicy chicken"}' -H "Content-Type: application/json"` returns results
- Multilingual queries (Arabic, French) work
- Backend `BE-006` proxy successfully calls and parses

**References**
- Backend issue BE-006

**Blocked By**
- SR-005

---

### ISSUE SR-007: Document & request backend sync hook for dish CRUD

**Description**
Backend doesn't currently sync menu changes to ChromaDB. After this issue, when `mayda-backend` creates/updates/deletes a dish, it should fire-and-forget a call to the search service's CRUD endpoints. This issue prepares search side (already done) + raises the backend-side counterpart.

**Goal**
Backend mutations propagate to ChromaDB; search results stay fresh.

**Targeted Files**
- `search/docs/sync-contract.md` (new)
- (Spawns sister issue on `mayda-backend`)

**Tasks**
- [ ] Write `docs/sync-contract.md`: documents POST/PUT/DELETE `/dishes` endpoints the backend should call
- [ ] Specify request/response shapes
- [ ] Specify recommended sync timing (after backend write succeeds; ignore failures, retry in background)
- [ ] Open issue in `mayda-backend` (suggested ID `BE-030`) titled "Sync dish mutations to mayda-ai/search" linking to this doc

**Acceptance Criteria**
- Sync contract doc clear + actionable
- Backend-side issue exists referencing the contract

**References**
- Existing CRUD: [search-llm/main.py:116-307](search-llm/main.py)

**Blocked By**
- SR-006

---

### ISSUE SR-008: Add healthcheck to docker-compose + logging upgrade

**Description**
`/health` endpoint exists in code but isn't wired into docker-compose. Also `print("ChromaDB initialized successfully")` should become structured logging.

**Goal**
Compose can verify service health; structured logs.

**Targeted Files**
- `search/docker-compose.yml`
- `search/app/main.py`
- `search/app/{chromadb_helper,model}.py`
- `search/requirements.txt`

**Tasks**
- [ ] Add `loguru==0.7.2` to `requirements.txt`
- [ ] Replace all `print()` with `logger.info()` / `logger.warning()` etc.
- [ ] Add `healthcheck` stanza to `docker-compose.yml`:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8102/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
  ```

**Acceptance Criteria**
- `docker compose ps` shows healthy/unhealthy
- Logs are structured (JSON in prod)

**References**
- AUDIT.md → "No healthcheck in docker-compose"

**Blocked By**
- SR-003

---

# 🟡 SERVICE: `inventory`

### ISSUE IN-001: Migrate folder + reorganize into package structure; archive notebook

**Description**
The service is currently a flat collection of CLI scripts with no package boundaries. Reorganize into `app/` package, move the Jupyter notebook to `notebooks/`, exclude from Docker build.

**Goal**
Clean package structure separating runtime code from notebooks.

**Targeted Files**
- `inventory/app/{forecaster,database,models,consumption}.py`
- `inventory/app/__init__.py`
- `inventory/notebooks/exploratory.ipynb` (from `test.ipynb`)
- `inventory/data/` (placeholder for SQLite volume)
- `inventory/scripts/{add_consumption,get_predictions}.py` (existing CLIs preserved)
- `inventory/.dockerignore`
- `inventory/.gitignore`

**Tasks**
- [ ] Create `app/` package
- [ ] Move `forecaster_db.py` → `app/forecaster.py`; extract SQLAlchemy models into `app/models.py`
- [ ] Move `database.py` → `app/database.py`
- [ ] Move `add_consumption.py` → `scripts/add_consumption.py` (keep as CLI tool)
- [ ] Move `get_predictions.py` → `scripts/get_predictions.py`
- [ ] Move `test.ipynb` → `notebooks/exploratory.ipynb`
- [ ] Create `data/` directory with `.gitkeep`
- [ ] Add `notebooks/`, `data/`, `*.db`, `__pycache__/`, `.venv/` to `.gitignore`
- [ ] Add `notebooks/`, `data/`, `tests/`, `*.ipynb` to `.dockerignore`
- [ ] Add `from app.models import FoodItem, ...` updates

**Acceptance Criteria**
- `python -m scripts.get_predictions` still works (legacy CLI preserved)
- `*.db` files not committed
- Notebook removed from Docker build context

**References**
- AUDIT.md → "Notebook in production repo"

**Blocked By**
- AI-001

---

### ISSUE IN-002: Create FastAPI shim with `POST /forecast` endpoint

**Description**
Inventory has zero HTTP surface today. Add a thin FastAPI app exposing `/forecast` (per-item) so the backend's `/ai/inventory/forecast` proxy (BE-007) has something to call.

**Goal**
Inventory service callable over HTTP; chef + manager dashboards can show predictions.

**Targeted Files**
- `inventory/api.py` (new)
- `inventory/app/schemas.py` (new — Pydantic models)
- `inventory/app/services/forecast_service.py` (new — wraps forecaster)

**Tasks**
- [ ] Create `api.py` with FastAPI app + `lifespan` that loads forecaster at startup (don't load per request)
- [ ] Add `POST /forecast` accepting `{item: str, date: ISO8601, weather?: str, special_event?: int}`
- [ ] Returns `{item, date, units, model_version, generated_at}`
- [ ] Add `GET /health`
- [ ] Add `GET /items` listing all known food items (for client autocomplete)
- [ ] Internal: `forecast_service.predict(item, date, weather, special_event)` wraps `DatabaseIntegratedForecaster.predict_consumption`
- [ ] CORS allowed for gateway only
- [ ] Forecaster instance held on `app.state`, not module-level

**Acceptance Criteria**
- `curl -X POST localhost:8103/forecast -d '{"item":"Tomatoes","date":"2026-05-23"}' -H "Content-Type: application/json"` returns prediction
- `/docs` shows endpoint
- `/health` returns 200
- Backend `BE-007` proxy successfully calls

**References**
- Backend issue BE-007
- AUDIT.md → "No HTTP server"

**Blocked By**
- IN-001

---

### ISSUE IN-003: Create Dockerfile + docker-compose entry (port 8103)

**Description**
No Dockerfile exists today. Create a slim Python 3.12 image; data volume for SQLite persistence.

**Goal**
Service deployable as a container; SQLite survives container restarts.

**Targeted Files**
- `inventory/Dockerfile` (new)
- `inventory/docker-compose.yml` (new)
- `inventory/.dockerignore`
- `inventory/README.md`

**Tasks**
- [ ] Dockerfile: `python:3.12-slim` base, install build deps (gcc for scikit-learn), pip install requirements, copy `app/`, expose 8103
- [ ] CMD `["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8103"]`
- [ ] Healthcheck: `curl -f http://localhost:8103/health || exit 1`
- [ ] Non-root user
- [ ] docker-compose with volume `./data:/data` mapped + port `"8103:8103"`
- [ ] `.env.example` with `DATABASE_URL=sqlite:////data/inventory.db`
- [ ] README dev commands

**Acceptance Criteria**
- `docker compose up` builds + starts the service
- SQLite persists across `docker compose down && docker compose up`
- Image size under 800MB

**References**
- AUDIT.md → "No Dockerfile, no docker-compose"

**Blocked By**
- IN-002

---

### ISSUE IN-004: Refactor `DatabaseIntegratedForecaster` to remove constructor side-effects

**Description**
The forecaster opens a long-lived SQLAlchemy session in `__init__` and relies on `__del__` to close it — fragile in async/concurrent contexts. Refactor to session-per-request via FastAPI dependency.

**Goal**
Forecaster doesn't own a session; sessions are scoped to requests.

**Targeted Files**
- `inventory/app/forecaster.py`
- `inventory/app/database.py`
- `inventory/api.py`

**Tasks**
- [ ] Remove `self.db = SessionLocal()` from `__init__`
- [ ] Remove `__del__` close
- [ ] Refactor methods to accept `db: Session` as parameter
- [ ] Add FastAPI dependency `get_db_session()` yielding session, closing on cleanup
- [ ] Cache trained models on `app.state.forecaster` (no DB binding)
- [ ] Route handlers receive both `forecaster` and `db` separately

**Acceptance Criteria**
- No DB session held outside request scope
- Parallel requests don't share session state
- Forecaster instance is stateless except for trained models

**References**
- AUDIT.md → "Constructor side effects + long-lived sessions"

**Blocked By**
- IN-002

---

### ISSUE IN-005: Persist trained model via `joblib`

**Description**
`train_models()` retrains from scratch on every CLI invocation. In an HTTP service, retraining on every request is unacceptable. Train once, serialize to disk, load at startup.

**Goal**
Sub-second model load at startup; admin-triggered retraining.

**Targeted Files**
- `inventory/app/forecaster.py`
- `inventory/api.py`
- `inventory/requirements.txt`
- `inventory/scripts/train_and_save.py` (new)

**Tasks**
- [ ] Add `joblib` to requirements
- [ ] Add `forecaster.save_models(path)` and `Forecaster.load_models(path)` class methods
- [ ] Lifespan tries to load from `MODEL_PATH` env var; if not present, trains from DB + saves
- [ ] Add `POST /admin/retrain` (admin-only — same `X-Service-Token` for now) that retrains + saves
- [ ] CLI script `scripts/train_and_save.py` for offline training

**Acceptance Criteria**
- Cold start under 5s once model is cached on disk
- Retraining endpoint works without restart
- Trained model file under 50MB

**References**
- AUDIT.md → "Model isn't persisted"

**Blocked By**
- IN-004

---

### ISSUE IN-006: Move SQLite to volume-mounted `/data` path

**Description**
Current `DATABASE_URL = "sqlite:///./restaurant_inventory.db"` is a relative path in CWD — file lost on container restart. Move to `/data/inventory.db` (absolute, volume-mounted).

**Goal**
SQLite persists across container restarts.

**Targeted Files**
- `inventory/app/database.py`
- `inventory/.env.example`
- `inventory/docker-compose.yml`

**Tasks**
- [ ] Change `DATABASE_URL` to read from `os.getenv("DATABASE_URL", "sqlite:////data/inventory.db")`
- [ ] Default for local dev: `sqlite:///./data/inventory.db`
- [ ] Default for Docker: `sqlite:////data/inventory.db` (set in compose env)
- [ ] Compose mounts `./data:/data`
- [ ] Document in README

**Acceptance Criteria**
- DB file persists across `docker compose restart`
- DB file persists across `docker compose down && up`
- Local dev still works (file in `./data/`)

**References**
- AUDIT.md → "SQLite database hardcoded"

**Blocked By**
- IN-001, IN-003

---

### ISSUE IN-007: Add service-token + CORS middleware

**Description**
Add shared service-token guard from AI-002 + CORS restricted to backend origin.

**Goal**
Only gateway-authenticated calls accepted.

**Targeted Files**
- `inventory/app/middleware/service_auth.py` (new)
- `inventory/api.py`
- `inventory/app/config.py` (new — settings)
- `inventory/.env.example`

**Tasks**
- [ ] Create `Settings` with `SERVICE_TOKEN`, `GATEWAY_ORIGIN`, `DATABASE_URL`, `MODEL_PATH`
- [ ] Create service-token dependency per AI-002 pattern
- [ ] Apply to all routes except `/health`
- [ ] Add CORS middleware in `api.py`

**Acceptance Criteria**
- Request without `X-Service-Token` returns 401
- `/health` still public
- CORS preflight from gateway origin succeeds

**References**
- AI-002

**Blocked By**
- AI-002, IN-002

---

### ISSUE IN-008: Pin deps, fix `datetime.utcnow()`, narrow warnings filter

**Description**
Three small code-quality fixes from the audit: pin all dependencies, replace deprecated `datetime.utcnow()`, and narrow the `warnings.filterwarnings('ignore')` to specific categories.

**Goal**
Reproducible builds; no deprecation warnings; warnings still surface real issues.

**Targeted Files**
- `inventory/requirements.txt`
- `inventory/app/forecaster.py`
- `inventory/app/models.py`

**Tasks**
- [ ] Pin every dep in `requirements.txt`: `sqlalchemy==2.0.23`, `pandas==2.1.3`, `numpy==1.25.2`, `scikit-learn==1.3.2`, plus new `fastapi==0.115.0`, `uvicorn[standard]==0.30.0`, `joblib==1.3.2`, `loguru==0.7.2`
- [ ] Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` throughout
- [ ] Replace `warnings.filterwarnings('ignore')` with category-scoped filters (e.g. `warnings.filterwarnings('ignore', category=FutureWarning)`)

**Acceptance Criteria**
- `pip freeze | diff requirements.txt` shows no version differences
- No `DeprecationWarning` on test runs
- Warnings still visible for new issues

**References**
- AUDIT.md → bottleneck patterns for inventory

**Blocked By**
- IN-001

---

### ISSUE IN-009: Add `POST /forecast/bulk` + `GET /recommendations/restock`

**Description**
Two convenience endpoints for the manager dashboard (MG-009): bulk forecast (avoid N round-trips when chef wants 20 items) + the audit-mentioned restock recommendations.

**Goal**
Manager UI can fetch all data in 2 calls, not 20.

**Targeted Files**
- `inventory/api.py`
- `inventory/app/schemas.py`
- `inventory/app/services/forecast_service.py`

**Tasks**
- [ ] `POST /forecast/bulk` accepts `{items: [{item, date, weather?, special_event?}, ...]}` returns `{forecasts: [...]}`
- [ ] `GET /recommendations/restock?days_ahead=7&safety_margin=0.2` wraps existing `generate_restock_recommendations`
- [ ] Both behind service-token

**Acceptance Criteria**
- Bulk forecast for 20 items returns in under 2s
- Restock recommendation matches existing CLI output structure

**References**
- Frontend issue MG-009
- Existing: [forecaster_db.py:46](Inventory_prediction/forecaster_db.py) (`generate_restock_recommendations`)

**Blocked By**
- IN-002, IN-005

---

# 🔴 SERVICE: `voice`

### ISSUE VC-001: Migrate folder + reorganize into package structure; archive `VoiceScript.py`

**Description**
Current code is one 243-line `VoiceScript.py` mixing model loading, mic capture, parsing, and the interactive loop. Reorganize into `app/` package and archive the original mic-bound interactive CLI in `legacy/`.

**Goal**
Reusable modules separated; legacy preserved but isolated.

**Targeted Files**
- `voice/app/{transcribe,chef_parser,order_parser}.py`
- `voice/app/__init__.py`
- `voice/legacy/VoiceScript.py` (moved)
- `voice/legacy/README.md`
- `voice/.dockerignore`
- `voice/.gitignore`

**Tasks**
- [ ] Create `app/` package
- [ ] Extract `transcribe(audio_bytes_or_path)` function into `app/transcribe.py` (no mic dependency)
- [ ] Extract `parse_chef_command()` + `calculate_similarity()` + number-word mapping into `app/chef_parser.py`
- [ ] Move full `VoiceScript.py` → `legacy/VoiceScript.py` with README explaining it was the interactive CLI version
- [ ] Add `legacy/`, `whisper-env/`, `logs/` to `.dockerignore`

**Acceptance Criteria**
- `from app.transcribe import transcribe` works
- `from app.chef_parser import parse_chef_command` works
- Legacy script preserved but not in Docker image

**References**
- AUDIT.md → "No reusable transcribe function"

**Blocked By**
- AI-001

---

### ISSUE VC-002: Create FastAPI shim with `POST /transcribe` (multipart upload)

**Description**
Backend's `/ai/voice/transcribe` proxy (BE-008) sends multipart audio. Service needs a FastAPI app accepting `audio: UploadFile`, calling `transcribe()`, returning JSON.

**Goal**
Audio upload → transcript JSON.

**Targeted Files**
- `voice/api.py` (new)
- `voice/app/schemas.py` (new)
- `voice/requirements.txt`

**Tasks**
- [ ] Add to requirements: `fastapi==0.115.0`, `uvicorn[standard]==0.30.0`, `python-multipart==0.0.9`
- [ ] Create `api.py` with FastAPI app
- [ ] `POST /transcribe` accepting `audio: UploadFile = File(...)`, optional `language: str | None = None` form field
- [ ] Save to temp file, pass to `transcribe()`, delete temp file
- [ ] Returns `{text, language, duration_seconds}`
- [ ] `GET /health` returns 200 (verifies Whisper loaded)
- [ ] CORS allowed for gateway only

**Acceptance Criteria**
- `curl -X POST localhost:8104/transcribe -F "audio=@test.m4a"` returns transcript
- 5-second clip transcribed in < 3s on CPU
- 30MB upload returns 413 Payload Too Large
- Backend `BE-008` proxy successfully calls

**References**
- Backend issue BE-008

**Blocked By**
- VC-001, VC-003

---

### ISSUE VC-003: Move Whisper load to `lifespan` + configurable model size

**Description**
Currently `whisper.load_model("medium")` runs at module import (15-30s cold start, ~1.5GB RAM). Move to `lifespan` startup so the load happens once and is observable. Make model size configurable via env (`tiny` for fast tests, `medium` for accuracy).

**Goal**
Model load is explicit, observable, configurable.

**Targeted Files**
- `voice/app/transcribe.py`
- `voice/api.py`
- `voice/app/config.py` (new)
- `voice/.env.example`

**Tasks**
- [ ] Add `WHISPER_MODEL: str = "medium"` to `Settings`
- [ ] Remove module-level `model = whisper.load_model(...)` from `transcribe.py`
- [ ] `transcribe.py` exposes a `Transcriber` class that holds the model
- [ ] Lifespan instantiates `Transcriber(model_size=settings.WHISPER_MODEL)`, stores on `app.state.transcriber`
- [ ] Routes get transcriber via `request.app.state`
- [ ] Document model size trade-offs (tiny: 75MB/fast/low-acc; medium: 1.5GB/slow/high-acc)

**Acceptance Criteria**
- Startup time visible in logs
- Setting `WHISPER_MODEL=tiny` reduces image RAM by ~1GB
- Endpoint works with both tiny and medium

**References**
- AUDIT.md → "Module-level model load"

**Blocked By**
- VC-001

---

### ISSUE VC-004: Drop `sounddevice` dependency; rewrite Dockerfile without portaudio

**Description**
The service no longer needs mic access (clients upload audio). Drop `sounddevice` from requirements and remove the `portaudio19-dev` + `libasound2-dev` system packages from the Dockerfile — saves ~30MB and simplifies the build.

**Goal**
Smaller Docker image; no audio-device dependencies.

**Targeted Files**
- `voice/requirements.txt`
- `voice/Dockerfile`

**Tasks**
- [ ] Remove `sounddevice` from requirements
- [ ] Remove `portaudio19-dev`, `libasound2-dev` from Dockerfile `apt-get install`
- [ ] Keep `libsndfile1` (needed by soundfile for audio file decoding)
- [ ] Remove `sounddevice` imports from any remaining source files (should already be in `legacy/`)
- [ ] Rebuild + measure image size

**Acceptance Criteria**
- Image size reduces by ≥20MB
- All audio file formats (m4a, wav, mp3) still decode

**References**
- AUDIT.md → "Dockerfile installs portaudio/libasound for mic capture — wasted bytes"

**Blocked By**
- VC-001

---

### ISSUE VC-005: Add `POST /parse/chef` using existing French command parser

**Description**
Surface the existing 90+ lines of French chef-command parsing logic (`parse_chef_command`) as an HTTP endpoint so the chef frontend (CH-008) can submit transcripts and get structured commands.

**Goal**
Chef-app voice commands parsed server-side with the same logic as the original CLI.

**Targeted Files**
- `voice/api.py`
- `voice/app/chef_parser.py`
- `voice/app/schemas.py`

**Tasks**
- [ ] Add `POST /parse/chef` accepting `{text: str}` returning `{type: "lance" | "prete" | null, order_number?: str, confidence?: int, matched_phrase?: str, message?: str}`
- [ ] Internally calls `parse_chef_command(text)`
- [ ] If `parse_chef_command` returns None → return `{type: null}`
- [ ] Service-token protected

**Acceptance Criteria**
- `POST /parse/chef` with `{"text": "commande 5 lance"}` returns `{type: "lance", order_number: "5", confidence: 100, ...}`
- Misrecognized text returns `{type: null}`
- French number words (`cinq`) recognized

**References**
- Frontend issue CH-008
- Existing: [VoiceScript.py:19-113](Voice-Chef---AI-Voice-Interface-for-Restaurant-Orders/VoiceScript.py)

**Blocked By**
- VC-001, VC-002

---

### ISSUE VC-006: Add `POST /parse/order` for mobile customer voice ordering

**Description**
Mobile app (MB-009) needs to convert "two burgers and a coke" into cart items. Build a new parser that takes transcript + menu items and fuzzy-matches.

**Goal**
Customer voice ordering: transcript → suggested cart entries.

**Targeted Files**
- `voice/app/order_parser.py` (new)
- `voice/app/schemas.py`
- `voice/api.py`

**Tasks**
- [ ] Create `order_parser.parse_order(text, menu_items)` returning list of `{menu_item_id, quantity, confidence}`
- [ ] Implementation: extract quantities (digits + words like "two"/"deux"/"اثنين"), fuzzy-match remaining tokens against menu item names with `SequenceMatcher`
- [ ] Reuse `calculate_similarity` from `chef_parser.py`
- [ ] Support English numbers in addition to French
- [ ] `POST /parse/order` accepting `{text, menu_items: [{id, name}]}` returning `{items: [...]}`
- [ ] Service-token protected

**Acceptance Criteria**
- `{text: "two burgers and a coke", menu_items: [{id:1, name:"Burger"}, {id:2, name:"Coke"}]}` returns 2× burger + 1× coke
- Unmatched phrases return empty `items: []`
- Works with French + English transcripts

**References**
- Frontend issue MB-009

**Blocked By**
- VC-002

---

### ISSUE VC-007: Add CORS + service-token middleware

**Description**
Apply the shared service-token guard from AI-002 + CORS restricted to backend origin.

**Goal**
Service rejects unauthorized requests; CORS limited.

**Targeted Files**
- `voice/app/middleware/service_auth.py` (new)
- `voice/api.py`
- `voice/app/config.py`
- `voice/.env.example`

**Tasks**
- [ ] Mirror AI-002 pattern in this service
- [ ] Apply to all routes except `/health`
- [ ] CORS in `api.py` restricted to `settings.GATEWAY_ORIGIN`

**Acceptance Criteria**
- Request without token → 401
- `/health` public
- CORS preflight from gateway succeeds

**References**
- AI-002

**Blocked By**
- AI-002, VC-002

---

### ISSUE VC-008: Replace `print()` with `loguru`; structured logging

**Description**
The 200+ lines of CLI code use `print()` extensively (emoji-tagged status). Service-mode needs structured logs. Replace all prints with `loguru`.

**Goal**
Structured logs (JSON in prod) with request-ID context.

**Targeted Files**
- `voice/app/{transcribe,chef_parser,order_parser}.py`
- `voice/api.py`
- `voice/requirements.txt`

**Tasks**
- [ ] Add `loguru==0.7.2` to requirements
- [ ] Configure logger in `app/logging.py` (JSON output if `ENV=production`)
- [ ] Replace every `print(...)` with `logger.info(...)` / `logger.warning(...)` etc.
- [ ] Inject request ID into log records via `loguru.contextualize` (after VC-007)

**Acceptance Criteria**
- No `print()` calls in `app/` or `api.py`
- Logs include level, timestamp, request_id

**References**
- AUDIT.md → "print() everywhere"

**Blocked By**
- VC-002

---

### ISSUE VC-009: Update healthcheck + docker-compose entry (port 8104)

**Description**
Current healthcheck verifies `whisper` lib imports — doesn't tell you if HTTP server is up. Fix healthcheck + standardize port + add to docker-compose.

**Goal**
Compose can verify real service health on port 8104.

**Targeted Files**
- `voice/docker-compose.yml`
- `voice/Dockerfile`
- `voice/README.md`

**Tasks**
- [ ] Dockerfile: `EXPOSE 8104`, change CMD to `["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8104"]`
- [ ] docker-compose: port mapping `"8104:8104"`, healthcheck: `["CMD", "curl", "-f", "http://localhost:8104/health"]`
- [ ] Remove `stdin_open: true, tty: true` (these were for interactive CLI)
- [ ] Update healthcheck `start_period` to 60s (model load time)
- [ ] Update README dev commands

**Acceptance Criteria**
- `docker compose up` brings service to healthy
- `curl localhost:8104/health` returns 200
- Container survives without TTY attached

**References**
- AUDIT.md → "Healthcheck checks import, not service health"

**Blocked By**
- VC-002, VC-004

---

## 📊 Summary

| Service | Issues | Hours | Critical Path |
|---|---|---|---|
| **Repo-level (AI-)** | 4 (AI-001…004) | 2 | AI-001 first |
| **recommendation (RC-)** | 8 (RC-001…008) | 4 | RC-003, RC-004 |
| **search (SR-)** | 8 (SR-001…008) | 4 | SR-002 (bug), SR-005, SR-006 |
| **inventory (IN-)** | 9 (IN-001…009) | 6 | IN-002, IN-003 (new HTTP service) |
| **voice (VC-)** | 9 (VC-001…009) | 6 | VC-002 (new HTTP service) |
| **TOTAL** | **38 issues** | **~22 hours** | |

**Critical 48h path:** AI-001 first → AI-002 in parallel with starting each service's first issue → IN-002 + VC-002 (highest priority — these unblock backend proxies BE-007 + BE-008) → SR-002 (audit-flagged duplicate-lifespan bug) → RC-003 (contract mismatch fix) → service-token middleware on all 4 (AI-002 dependents) → AI-004 (root compose) last.

**Recommended parallelization:** One dev per service. Recommendation + search can land in 4 hours each (they're HTTP services already). Inventory + voice take 6 hours each (HTTP wrapper from scratch). Total wall-clock: ~6 hours with 4 devs, ~22 hours with 1.

**Hard cross-repo dependencies:**
- BE-005 ↔ RC-003 (recommendation contract)
- BE-006 ↔ SR-006 (search endpoint)
- BE-007 ↔ IN-002 (inventory endpoint must exist)
- BE-008 ↔ VC-002 (voice endpoint must exist)
- All 4 service-token issues depend on backend's `SERVICE_TOKEN` env being set (BE-004)

That closes out the AI tier. Ready for the `mayda-infra` and `mayda-docs` plans, or want me to verify any of these issues against the actual source first?