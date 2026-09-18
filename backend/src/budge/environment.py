"""What this particular deployment is allowed to reach.

Vercel sets VERCEL_ENV to "production", "preview" or "development" on every
deployment, which is the only thing that reliably distinguishes them from
inside the running function.
"""

import os

PREVIEW = "preview"
ESCAPE_HATCH = "ALLOW_AKAHU_IN_PREVIEW"
DEMO_SWITCH = "BUDGE_DEMO"


def vercel_env() -> str:
    return os.environ.get("VERCEL_ENV", "development")


def demo_enabled() -> bool:
    """Whether the invented people exist on this deployment.

    A switch rather than an inference. It used to be "anywhere but production",
    which was wrong in both directions: it put the demo on every deployment
    nobody had thought about, and it left no way to run a demo somewhere people
    can actually reach without a login wall. Set BUDGE_DEMO=1 where the demo is
    wanted, and nowhere else.
    """
    return os.environ.get(DEMO_SWITCH) == "1"


def akahu_enabled() -> bool:
    """False where a real bank has no business being reached.

    Two cases. A preview is the most exposed thing we ship: every branch and
    every draft gets one, built from whatever was pushed, and they share
    production's database and encryption key, so without this a preview could
    decrypt a real user's Akahu tokens and read their transactions.

    A deployment running the demo is the second. Invented people and real bank
    credentials do not belong in the same database, and a demo is something you
    hand round, so it is the last place a live token should sit. Turn the demo
    off before connecting a real bank.

    ALLOW_AKAHU_IN_PREVIEW=1 lifts the preview half, for a preview that has a
    database and an encryption key of its own. Nothing lifts the demo half.
    """
    if demo_enabled():
        return False
    return vercel_env() != PREVIEW or os.environ.get(ESCAPE_HATCH) == "1"
