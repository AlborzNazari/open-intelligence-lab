#!/usr/bin/env python3
"""
scripts/create_user.py — create an Open Intelligence Lab user from the command line.

Public POST /auth/register only ever creates analysts, and there is no API path
to create the FIRST admin. This script is that path: it calls the same
register_user() the API uses, but can pass allow_admin=True.

Run it from the repo root so `backend` is importable, and point OIL_USER_DB at
the same database the server uses (default: ./oil_users.db).

Examples
--------
  # an analyst
  python -m scripts.create_user alice s3cretpass "Alice Analyst"

  # the first admin (no API can do this)
  python -m scripts.create_user root adminpass99 "Root Admin" --role admin

  # against a specific database file
  OIL_USER_DB=/data/oil_users.db python -m scripts.create_user bob bobpass99 "Bob"

Note on Fly.io: the SQLite file lives on the container's ephemeral filesystem
unless you attach a volume and set OIL_USER_DB to a path on it. Without a volume,
accounts created here (or via /auth/register) do not survive a redeploy.
"""

import argparse
import sys

from backend.auth import init_db, register_user


def main() -> int:
    ap = argparse.ArgumentParser(description="Create an Open Intelligence Lab user account.")
    ap.add_argument("username", help="login username (1–64 chars, unique)")
    ap.add_argument("password", help="password (at least 8 chars)")
    ap.add_argument("full_name", help="display name (1–128 chars)")
    ap.add_argument("--role", choices=["analyst", "admin"], default="analyst",
                    help="account role (default: analyst)")
    args = ap.parse_args()

    init_db()
    try:
        user = register_user(
            args.username,
            args.password,
            args.full_name,
            role=args.role,
            allow_admin=(args.role == "admin"),
        )
    except Exception as exc:  # register_user raises HTTPException on bad input / duplicate
        detail = getattr(exc, "detail", str(exc))
        print(f"error: {detail}", file=sys.stderr)
        return 1

    print(f"created {user['role']}: {user['username']} ({user['full_name']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
