"""What this particular deployment is allowed to reach.

Vercel sets VERCEL_ENV to "production", "preview" or "development" on every
deployment, which is the only thing that reliably distinguishes them from
inside the running function.
"""

import os

PREVIEW = "preview"
ESCAPE_HATCH = "ALLOW_AKAHU_IN_PREVIEW"


def vercel_env() -> str:
    return os.environ.get("VERCEL_ENV", "development")


def akahu_enabled() -> bool:
    """False on preview deployments, so no preview can reach a real bank.

    A preview is the most exposed thing we ship: every branch and every draft
    gets one, built from whatever was pushed, and today they share production's
    database and encryption key. Without this, a preview could decrypt a real
    user's Akahu tokens and read their transactions.

    Set ALLOW_AKAHU_IN_PREVIEW=1 on a preview that genuinely needs Akahu, and
    only once it has a database and an encryption key of its own.
    """
    return vercel_env() != PREVIEW or os.environ.get(ESCAPE_HATCH) == "1"
