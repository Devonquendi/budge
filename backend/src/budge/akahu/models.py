"""Domain models for Akahu data."""

from decimal import Decimal

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    type: str
    connection_name: str
    formatted_account: str | None = None
    currency: str
    # Money is Decimal end to end: floats don't add up to totals that reconcile.
    # Pydantic serialises these as JSON strings, so the browser gets the exact
    # digits Akahu sent and decides for itself how to add them up.
    balance_current: Decimal
    balance_available: Decimal | None = None
