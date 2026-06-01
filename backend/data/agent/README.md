# Agent knowledge & scripted behavior artifacts

Structured content for the **knowledge-grounded QA** slice of the bounded context (`raya_faraz_agent.ai_agent`).

| Path | YAML key (`backend/config/*.yaml`) | Purpose |
| --- | --- | --- |
| `knowledge/company-overview.en.md` | `qa_agent.knowledge_document` | Authoritative factual briefing (English) used as the grounding corpus. Swap or extend freely. |
| `knowledge/company-overview.fa.original.txt` | _(archival)_ | Original Persian source excerpt preserved for auditing and re-translation workflows. |
| `instructions.md` | `qa_agent.behavior_instructions` | **Your script / acting notes** describing ordering (“say X, then say Y”), tone, disclaimers—whatever product owners need the agent to follow in addition to the facts. |

`max_history_messages` (default **13**) governs how many prior chat turns survive when calling `POST /api/v1/chat/qa`.

All YAML paths resolve relative to `backend/` (the directory beside `Dockerfile/` and `docker-compose.yml` volumes).
