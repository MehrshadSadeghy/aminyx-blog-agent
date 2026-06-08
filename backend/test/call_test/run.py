"""Run API call tasks against a live agent service.

Usage:
    cd backend
    ADMIN_API_KEY=your-key python -m call_test.run

Optional:
    AGENT_BASE_URL=http://localhost:8085
    python -m call_test.run --wait   # poll until jobs complete or timeout
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from call_test.tasks import print_outcomes, run_user_flow


def main() -> int:
    parser = argparse.ArgumentParser(description="Call agent APIs like the Aminyx backend.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AGENT_BASE_URL", "http://localhost:8085"),
        help="Agent base URL (default: AGENT_BASE_URL or http://localhost:8085)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ADMIN_API_KEY", ""),
        help="Bearer token (default: ADMIN_API_KEY env var)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll jobs until complete/fail instead of stopping at pending",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("ADMIN_API_KEY is required (env var or --api-key).", file=sys.stderr)
        return 1

    print(f"Target: {args.base_url}")
    print(f"Wait for completion: {args.wait}")
    print("-" * 60)

    outcomes = asyncio.run(
        run_user_flow(
            base_url=args.base_url,
            api_key=args.api_key,
            wait_for_complete=args.wait,
        )
    )
    failed = print_outcomes(outcomes)
    print("-" * 60)
    print(f"Done: {len(outcomes) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
