#!/usr/bin/env python3
"""Safely summarize ChatGPT/Codex rate-limit reset credits."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_URL = "https://chatgpt.com/backend-api/wham/rate-limit-reset-credits"


def load_access_token(auth_path: Path) -> str:
    try:
        auth = json.loads(auth_path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError("~/.codex/auth.json not found.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("~/.codex/auth.json is not valid JSON.") from exc

    token = auth.get("tokens", {}).get("access_token")
    if not isinstance(token, str) or not token.strip():
        raise RuntimeError("tokens.access_token not found in ~/.codex/auth.json.")
    return token


def local_time_text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1_000_000_000_000 else value
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    else:
        text = str(value).strip()
        if not text:
            return None
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return text
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    local = dt.astimezone()
    offset = local.strftime("%z")
    if len(offset) == 5:
        offset = f"{offset[:3]}:{offset[3:]}"
    return local.strftime("%Y-%m-%d %H:%M:%S ") + offset


def find_credit_list(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    for key in ("credits", "rate_limit_reset_credits", "reset_credits", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def summarize(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        if "available_count" in data:
            available_count = data["available_count"]
        else:
            available_count = data.get("availableCount")
    else:
        available_count = None

    credits = []
    for credit in find_credit_list(data):
        if not isinstance(credit, dict):
            continue
        credits.append(
            {
                "status": credit.get("status"),
                "title": credit.get("title"),
                "granted_at": local_time_text(credit.get("granted_at")),
                "expires_at": local_time_text(credit.get("expires_at")),
            }
        )

    return {"available_count": available_count, "credits": credits}


def fetch_summary(auth_path: Path, url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    token = load_access_token(auth_path)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Codex local rate-limit-credit check",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return 401, {"error": "HTTP 401: 凭证失效或没有正确携带 Authorization header。"}
        return exc.code, {"error": f"HTTP {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return 0, {"error": f"Network error: {exc.reason}"}
    except TimeoutError:
        return 0, {"error": f"Network timeout after {timeout:g} seconds."}

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return 0, {"error": "Response was not valid JSON."}

    return 200, summarize(data)


def print_table(summary: dict[str, Any]) -> None:
    if "error" in summary:
        print(summary["error"])
        return

    print(f"available_count: {summary.get('available_count')}")
    rows = summary.get("credits") or []
    if not rows:
        print("credits: []")
        return

    headers = ["status", "title", "granted_at", "expires_at"]
    widths = {
        header: max(len(header), *(len(str(row.get(header) or "")) for row in rows))
        for header in headers
    }
    print(" | ".join(header.ljust(widths[header]) for header in headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(" | ".join(str(row.get(header) or "").ljust(widths[header]) for header in headers))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely summarize rate-limit reset credits from the local Codex auth token."
    )
    parser.add_argument(
        "--auth-json",
        default=str(Path.home() / ".codex" / "auth.json"),
        help="Path to auth.json. Defaults to ~/.codex/auth.json.",
    )
    parser.add_argument("--url", default=API_URL, help="Endpoint URL.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds.")
    parser.add_argument("--format", choices=("json", "table"), default="json")
    args = parser.parse_args()

    try:
        _status, summary = fetch_summary(Path(args.auth_json), args.url, args.timeout)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.format == "table":
        print_table(summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0 if "error" not in summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
