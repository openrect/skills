---
name: check-rate-limit-reset-credits
description: Safely check ChatGPT/Codex WHAM rate-limit reset credits using the local Codex credential in ~/.codex/auth.json. Use when the user asks to inspect rate-limit reset credits, reset-credit availability, WHAM credits, Codex or ChatGPT limit reset credits, or to call https://chatgpt.com/backend-api/wham/rate-limit-reset-credits without exposing tokens, cookies, or full unique IDs.
---

# Check Rate-Limit Reset Credits

## Workflow

Use `scripts/check_rate_limit_reset_credits.py` for the check unless the user explicitly asks for a different implementation.

```bash
python scripts/check_rate_limit_reset_credits.py
```

The script reads `~/.codex/auth.json`, extracts only `tokens.access_token`, and sends it as `Authorization: Bearer <token>` to:

```text
https://chatgpt.com/backend-api/wham/rate-limit-reset-credits
```

## Safety Rules

- Do not print `access_token`, `refresh_token`, cookies, raw `auth.json`, raw API responses, or complete unique IDs.
- Summarize only `available_count` and each credit's `status`, `title`, `granted_at`, and `expires_at`.
- Convert `granted_at` and `expires_at` from UTC to the machine's local timezone before presenting them.
- If the API returns HTTP 401, tell the user: `凭证失效或没有正确携带 Authorization header。`
- For other non-2xx statuses, report only the status code and reason unless the user explicitly asks for deeper debugging.

## Output

Prefer a concise table or short JSON summary. Do not include fields outside the allowed summary fields.

If the script cannot run, reproduce the same workflow with local shell tools while preserving all safety rules above.
