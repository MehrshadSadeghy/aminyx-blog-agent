# Endpoint Test Plan

## Endpoints Covered

| Method | Path | Test file |
|--------|------|-----------|
| GET | `/health` | `test_health_endpoints.py` |
| POST | `/api/v1/agent/suggestions` | `test_agent_suggestion_endpoints.py` |
| GET | `/api/v1/agent/suggestions/{job_id}` | `test_agent_suggestion_endpoints.py` |
| POST | `/api/v1/agent/strategy-content` | `test_strategy_content_endpoints.py` |
| GET | `/api/v1/agent/strategy-content/{job_id}` | `test_strategy_content_endpoints.py` |

## Dependency Graph (API layer)

```
health_check
create_suggestion_job -> get_suggestion_service -> SuggestionAgentService.create_job
get_suggestion_job_status -> get_suggestion_service -> SuggestionAgentService.get_job
create_strategy_content_job -> get_strategy_content_service -> StrategyContentAgentService.create_job
get_strategy_content_job_status -> get_strategy_content_service -> StrategyContentAgentService.get_job
require_bearer -> Config.resolved_admin_api_key (all /api/v1/agent/* routes)
```

## Cyclomatic Complexity Summary

| Function | CC | Main paths | Risk |
|----------|----|------------|------|
| `health_check` | 1 | ok | low |
| `require_bearer` | 4 | no key / no header / bad token / ok | medium |
| `create_suggestion_job` | 1 | success | low |
| `get_suggestion_job_status` | 2 | found / 404 | low |
| `create_strategy_content_job` | 1 | success | low |
| `get_strategy_content_job_status` | 2 | found / 404 | low |
| `SuggestionJobRepositoryRedis.*` | 1–3 | see `test/crud/` | medium |
| `StrategyContentJobRepositoryRedis.*` | 1–3 | see `test/crud/` | medium |

## Run Command

`docker compose run` does **not** expand shell globs. Use one of these:

```bash
# Recommended — pytest.ini already targets crud + endpoint tests
docker compose -f docker-compose.local.yml --env-file .env run --rm --no-deps backend \
  pytest -c test/pytest.ini -v

# Or explicit file list (no glob)
docker compose -f docker-compose.local.yml --env-file .env run --rm --no-deps backend \
  pytest test/crud test/test_health_endpoints.py test/test_agent_suggestion_endpoints.py \
         test/test_strategy_content_endpoints.py test/test_system_endpoints.py \
         -c test/pytest.ini -v

# Glob only works inside sh -c
docker compose -f docker-compose.local.yml --env-file .env run --rm --no-deps backend \
  sh -c 'pytest test/crud test/test_*_endpoints.py -c test/pytest.ini -v'
```

After pulling test files to the server, rebuild the image so they are copied into the container:

```bash
docker compose -f docker-compose.local.yml build --no-cache backend
```

## Coverage Notes

- **Unit**: endpoint handlers and auth with mocked services (`@pytest.mark.unit`)
- **Integration**: Redis repositories via fakeredis (`@pytest.mark.integration`)
- **System**: multi-step HTTP workflows (`@pytest.mark.system`)

## Missing Testability Concerns

- `process_job` worker paths (Gemini, callbacks) are not covered here — they need Gemini/callback mocks in a separate service test module.
- Live Redis / live server E2E remains in `call_test/` for deployed environments.

## Refactoring Suggestions

- Extract a shared `create_api_test_app()` in production code if test app wiring diverges from `app.py`.
- Consider `callbackUrl`-only payload variant tests (currently only `callback` object is exercised).
