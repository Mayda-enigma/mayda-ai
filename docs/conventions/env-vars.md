# Standard environment variables

Every endpoint exposed by `mayda-ai` reads its configuration from environment
variables (loaded via `.env` in dev, real env in prod). The following are
**mandatory**; absence in production is a deploy-blocker.

| Var | Required | Purpose | Example |
|---|---|---|---|
| `SERVICE_TOKEN` | yes (prod) | Shared secret validated on every inbound request. Forwarded on outbound backend calls. See [service-token.md](service-token.md). | `change-me-in-prod` |
| `LOG_LEVEL` | no (default `INFO`) | Python `logging` level. Use `DEBUG` locally. | `INFO` |
| `PORT` | no (default `8101`) | Port `uvicorn` binds to. | `8101` |

## Service-specific vars

The consolidated `src/` app also reads:

| Var | Purpose |
|---|---|
| `BACKEND_API_URL` | URL of `mayda-backend` for outbound RPC. |
| `BACKEND_API_TIMEOUT` | HTTP timeout in seconds (default `30`). |
| `LLM_PROVIDER`, `LLM_MODEL`, `GEMINI_API_KEY`, `OPENAI_API_KEY` | LLM selection for the recommendation engine. |
| `LLM_TEMPERATURE`, `LLM_MAX_TOKENS` | Generation parameters. |
| `GATEWAY_ORIGIN` | Single allowed CORS origin. See [cors.md](cors.md). |
| `CHROMA_DB_DIR`, `CHROMA_COLLECTION_NAME` | Vector store location for the search engine. |
| `INVENTORY_DATABASE_URL`, `INVENTORY_MODEL_PATH` | SQLite URL and joblib path for the inventory forecaster. |
| `WHISPER_MODEL` | Whisper model size (`tiny`, `base`, `small`, ...) for voice transcription. |

The full schema with defaults is at
[src/core/config.py](../../src/core/config.py). The dev template lives in
[.env.example](../../.env.example).

## Rules

- **Never** commit real secrets — only `.env.example` may be in git.
- **Never** hardcode any value listed here in source. Read it through
  `src.core.config.settings`.
- `.env` is git-ignored at the repo root.
